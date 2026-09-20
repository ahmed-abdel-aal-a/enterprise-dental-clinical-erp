"""Orchestrator bridge — wires a conversation to the core engine.

Builds the :class:`AgentContext` (permissions = the caller's own, a
guardrail config that defers writes to inline confirmation, audit linked
to the core agent session), reconstructs the message history, drives
``run_turn``, persists the new messages, and yields ``TurnEvent``s that
the router frames as SSE. Provider is injectable for tests.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.agents.context import AgentContext, AgentMode
from app.core.agents.guardrails import GuardrailConfig
from app.core.agents.orchestrator import ConfirmationRequired, ToolCallFinished, TurnUsage, run_turn
from app.core.agents.redaction import Redactor
from app.core.agents.tools.registry import tool_registry
from app.core.auth.permissions import permission_matches
from app.core.llm.base import ProviderMessage, Role, TextBlock, ToolResultBlock, ToolUseBlock
from app.core.llm.factory import get_provider

from .models import CopilotConversation, CopilotSettings
from .serde import message_from_row
from .service import ClinicBudgetGuard, ConversationService

_BASE_PROMPT = (
    "أنت المساعد الذكي لنظام دنت أبيكس (DentApex)، مساعد لإدارة عيادة الأسنان. "
    "تجيب دائماً باللغة العربية الفصحى، بإيجاز ودقة ومهنية طبية وإدارية رفيعة، مع الفهم التام للعامية المصرية ومختلف اللهجات العربية والتفاعل معها بمرونة وسرعة دون تردد. استخدم الأدوات "
    "المتاحة للاستعلام والتفاعل مع بيانات العيادة؛ لا تخترع معلومات غير موجودة في الأدوات. بالنسبة للإجراءات "
    "التي تعدل البيانات (إنشاء، حجز، إلغاء، فوترة) استدعِ الأداة المناسبة فوراً: سيطلب النظام تأكيد المستخدم قبل "
    "تنفيذها. لا تفترض أبداً صلاحيات ليست لديك. "
    "الفواتير والمبالغ المحصلة محاور محاسبية منفصلة: أبلغ عن كل محور بشكل منفصل عند الطلب."
)

# Multi-step recipes the model chains with its own tool calls.
_PLAYBOOKS = (
    "\n\nالمهام الإرشادية المعتادة (قم بربط الأدوات بنفسك؛ إذا كانت تنقصك أداة لخطوة معينة، اذكر ذلك وتابع مع الباقي):\n"
    "- الموجز اليومي للعيادة (Briefing): get_day_overview(اليوم) → list_due_recalls(overdue=true) → "
    "list_budgets(status=['sent']). لخص البيانات في ثلاثة أقسام: المواعيد، الاتصالات والمتابعات المعلقة، والميزانيات بانتظار الرد.\n"
    "- تحضير زيارة مريض: get_patient → موعده (get_appointment أو get_day_overview) → list_due_recalls(patient_id) → "
    "list_budgets(patient_id, status=['sent','accepted']) → "
    "patient_payment_history. اعرض ملخصاً واضحاً للمريض.\n"
    "- تغطية موعد شاغر بسبب إلغاء: بعد إلغاء الموعد cancel_appointment (أو عند ذكر موعد متاح) → list_due_recalls(overdue=true)، رتب حسب "
    "priority=high → اقترح 2-3 مرشحين مع أرقام هواتفهم → عند تأكيد المستخدم: book_appointment → log_contact_attempt.\n"
    "- إنشاء فاتورة لمريض (Create Invoice): إذا لم يكن لديك معرف المريض، ابحث عنه عبر search_patients → استدعِ create_invoice مباشرة مع تحديد البنود والأسعار والفرع ليطلب النظام تأكيد الطبيب."
)

SYSTEM_PROMPT = _BASE_PROMPT + _PLAYBOOKS


async def build_system_prompt(db: AsyncSession, clinic_id: UUID) -> str:
    """Build dynamic system prompt enriched with live clinic name, branches, doctors, and timezone."""
    from datetime import datetime
    from sqlalchemy import select
    from app.core.auth.models import Clinic, ClinicMembership, User
    from app.core.branches.models import ClinicBranch
    from app.modules.agenda.tz import get_clinic_tz

    # 1. Clinic Name & Timezone
    clinic = await db.scalar(select(Clinic).where(Clinic.id == clinic_id))
    clinic_name = clinic.name if clinic else "العيادة"
    clinic_tz = await get_clinic_tz(db, clinic_id)
    now_local = datetime.now(clinic_tz)
    now_human = now_local.strftime("%Y-%m-%d %I:%M %p")
    arabic_days = ["الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
    today_name = arabic_days[now_local.weekday()]

    # 2. Active Branches
    b_stmt = (
        select(ClinicBranch)
        .where(ClinicBranch.clinic_id == clinic_id, ClinicBranch.is_active.is_(True))
        .order_by(ClinicBranch.is_main.desc(), ClinicBranch.display_order.asc())
    )
    b_rows = (await db.execute(b_stmt)).scalars().all()

    # 3. Active Professionals
    p_stmt = (
        select(
            User.id,
            User.first_name,
            User.last_name,
            ClinicMembership.role,
            ClinicBranch.name.label("branch_name"),
        )
        .join(ClinicMembership, ClinicMembership.user_id == User.id)
        .outerjoin(ClinicBranch, ClinicBranch.id == ClinicMembership.default_branch_id)
        .where(
            ClinicMembership.clinic_id == clinic_id,
            ClinicMembership.is_professional.is_(True),
            User.is_active.is_(True),
        )
    )
    p_rows = (await db.execute(p_stmt)).all()

    context_lines = [
        "\n\n[سياق العيادة الحالي والحي]:",
        f"- اسم العيادة: {clinic_name}",
        f"- التوقيت واليوم الحالي في العيادة: {today_name} {now_human} (المنطقة الزمنية: {clinic_tz.key}).",
        f"- قاعدة التوقيت الإلزامية (Timezone & DST): جميع التواريخ والأوقات يجب أن تُرسل بصيغة ISO 8601 متضمنة الإزاحة الزمنية (Offset) الصحيحة للتاريخ والوقت المطلوب حجز موعد فيه.",
        f"  انتبه بشدة لقواعد التوقيت الصيفي والشتوي (Daylight Saving Time) في منطقة {clinic_tz.key} عند تحديد المواعيد المستقبلية.",
        "  ممنوع استخدام حرف Z نهائياً في التواريخ، بل استخدم الإزاحة الرقمية الدقيقة (مثال: +02:00 أو +03:00 حسب ما يتوافق مع التاريخ والوقت المستهدف في هذه المنطقة الزمنية).",
        "- قاعدة استيعاب اللهجة العامية والمبادرة الفورية (Proactivity & Dialect):",
        "  * استوعب فوراً كافة صيغ الحديث بالعامية المصرية ومختلف اللهجات العربية والعبارات غير الرسمية المعتادة في العيادات (مثال: 'احجز لمعتز كشف بكره الساعه 7 مسائا', 'اعملي فاتورة للمريض بـ 500 جنيه كشف', 'ظبطلي معاد لمحمد أحمد', 'تمام كده').",
        "  * ممنوع التردد أو التوقف أو الانتظار؛ بادر دائماً واستدعِ الأداة المناسبة فوراً ليقوم النظام بعرض بطاقة التأكيد على المستخدم.",
        "  * إذا طُلِب إجراء لمريض دون تحديد معرفه (UUID)، ابحث عنه أولاً باستخدام أداة 'patients.search_patients' بالاسم المذكور في رسالة المستخدم.",
        "- قدرات الفوترة (Invoicing from Scratch):",
        "  * يمكنك إنشاء مسودات الفواتير من الصفر مباشرة باستخدام أداة 'billing.create_invoice'.",
        "  * إذا طلب المستخدم عمل فاتورة لمريض وحدد المبلغ أو الإجراء (مثلاً: 'اعمل فاتورة للمريض كشف بـ 500 جنيه')، جهز بند الفاتورة بالسعر والوصف المطلوب واستدعِ create_invoice فوراً دون أن تقول أنك لا تستطيع.",
    ]

    # Branches context & rules
    if b_rows:
        b_descs = [
            f"{b.name} (كود: {b.code}{' - الفرع الرئيسي' if b.is_main else ''}, معرف: {b.id})"
            for b in b_rows
        ]
        context_lines.append(f"- الفروع المتاحة ({len(b_rows)}): " + " | ".join(b_descs))
        if len(b_rows) == 1:
            context_lines.append(
                f"  * قاعدة الفروع: يوجد فرع وحيد نشط وهو '{b_rows[0].name}'. اعتمده تلقائياً في أي حجز موعد أو فاتورة دون سؤال المستخدم."
            )
        else:
            context_lines.append(
                "  * قاعدة الفروع: توجد فروع متعددة. اسأل المريض أو المستخدم عن الفرع المطلوب قبل تأكيد الإجراء."
            )
    else:
        context_lines.append("- الفروع المتاحة: لم تسجل فروع بعد.")

    # Professionals context & rules
    if p_rows:
        p_descs = [
            f"د. {r.first_name} {r.last_name} (الدور: {r.role}, الفرع: {r.branch_name or 'العام'}, معرف: {r.id})"
            for r in p_rows
        ]
        context_lines.append(f"- الأطباء والمعالجون المسجلون ({len(p_rows)}): " + " | ".join(p_descs))
        if len(p_rows) == 1:
            only_pro = p_rows[0]
            context_lines.append(
                f"  * قاعدة الأطباء: الطبيب المعالج والأساسي المسجل في العيادة هو 'د. {only_pro.first_name} {only_pro.last_name}'. "
                f"اعتمده تلقائياً وبشكل مباشر عند حجز أي موعد أو استعلام سريري دون الحاجة لسؤال المريض عن اسم الدكتور."
            )
        else:
            context_lines.append(
                "  * قاعدة الأطباء: يوجد أكثر من طبيب معالج بالعيادة. اسأل المريض عن الطبيب المطلوب أو التخصص قبل إتمام الحجز."
            )
    else:
        context_lines.append(
            "- الأطباء والمعالجون: لا يوجد أطباء مسجلون حالياً بصلاحية الكشف. وجه المستخدم لتفعيل خيار الطبيب المعالج من الإعدادات."
        )

    context_lines.append(
        "- توجيهات عامة: عند حجز موعد (agenda.book_appointment)، تحقق دائماً من توفر المريض والطبيب والوقت، ولخص بيانات الحجز بوضوح في طلب التأكيد."
    )

    return _BASE_PROMPT + "\n".join(context_lines) + _PLAYBOOKS

# Copilot gates writes via inline confirmation (a turn-level pause), so
# the approval-queue triggers are disabled. Rate limits + denylist stay.
COPILOT_GUARDRAILS = GuardrailConfig(
    require_approval_for=[],
    auto_require_approval_for_destructive=False,
    blocked_tools=[],
)


def _tool_names_for(permissions: list[str], *, include_free_text: bool = True) -> list[str]:
    """Registry tools the caller is allowed to use (AND of permissions).

    With ``include_free_text=False`` (redaction on), tools flagged
    ``exposes_free_text`` are excluded — their prose results can't be
    tokenized, so they never reach the cloud provider.
    """
    out: list[str] = []
    for name in tool_registry.list():
        tool = tool_registry.get(name)
        if tool is None:
            continue
        if not include_free_text and tool.exposes_free_text:
            continue
        if all(
            any(permission_matches(req, granted) for granted in permissions)
            for req in tool.permissions
        ):
            out.append(name)
    return out


def _build_context(
    *,
    db: AsyncSession,
    clinic_id: UUID,
    permissions: list[str],
    user_id: UUID,
    agent_id: UUID,
    session_id: UUID,
) -> AgentContext:
    return AgentContext(
        agent_id=agent_id,
        session_id=session_id,
        clinic_id=clinic_id,
        mode=AgentMode.AUTONOMOUS,  # writes gated by inline confirm, not the queue
        permissions=permissions,
        tools=tool_registry,
        db=db,
        supervisor_id=user_id,
        guardrail_config=COPILOT_GUARDRAILS,
    )


def _redactor_for(conv: CopilotConversation, settings_row: CopilotSettings) -> Redactor:
    r = Redactor(enabled=settings_row.redaction_enabled)
    r.seed(conv.context)
    return r


async def _history(db: AsyncSession, conv: CopilotConversation) -> list[ProviderMessage]:
    rows = await ConversationService.list_messages(db, conv.id)
    return [message_from_row(m.role, m.content) for m in rows]


async def _persist_tail(
    db: AsyncSession, conv: CopilotConversation, history: list[ProviderMessage], start: int
) -> None:
    for msg in history[start:]:
        await ConversationService.append_message(db, conv, role=msg.role.value, blocks=msg.content)


async def drive_turn(
    *,
    db: AsyncSession,
    conv: CopilotConversation,
    settings_row: CopilotSettings,
    permissions: list[str],
    user_id: UUID,
    agent_id: UUID,
    session_id: UUID,
    user_text: str,
    provider=None,
) -> AsyncIterator:
    """Append the user message, run one turn, persist + yield events."""
    history = await _history(db, conv)
    user_msg = ProviderMessage(Role.USER, [TextBlock(user_text)])
    await ConversationService.append_message(db, conv, role="user", blocks=user_msg.content)
    history.append(user_msg)

    provider = provider or get_provider(conv.provider)
    redactor = _redactor_for(conv, settings_row)
    budget = ClinicBudgetGuard(settings_row, conv)
    ctx = _build_context(
        db=db,
        clinic_id=conv.clinic_id,
        permissions=permissions,
        user_id=user_id,
        agent_id=agent_id,
        session_id=session_id,
    )

    system_prompt = await build_system_prompt(db, conv.clinic_id)
    start = len(history)
    async for ev in run_turn(
        ctx=ctx,
        provider=provider,
        system=system_prompt,
        history=history,
        tool_names=_tool_names_for(permissions, include_free_text=not redactor.enabled),
        redactor=redactor,
        model=conv.model,
        max_tokens=4096,
        budget=budget,
    ):
        yield ev
    await _persist_tail(db, conv, history, start)


async def resume_turn(
    *,
    db: AsyncSession,
    conv: CopilotConversation,
    settings_row: CopilotSettings,
    permissions: list[str],
    user_id: UUID,
    agent_id: UUID,
    session_id: UUID,
    call_id: str,
    approve: bool,
    provider=None,
) -> AsyncIterator:
    """Execute (or skip) the pending tool, then resume the turn."""
    history = await _history(db, conv)
    pending = _find_pending(history, call_id)
    if pending is None:
        return

    provider = provider or get_provider(conv.provider)
    redactor = _redactor_for(conv, settings_row)
    budget = ClinicBudgetGuard(settings_row, conv)
    ctx = _build_context(
        db=db,
        clinic_id=conv.clinic_id,
        permissions=permissions,
        user_id=user_id,
        agent_id=agent_id,
        session_id=session_id,
    )

    if approve:
        res = await ctx.tools.call(ctx, pending.name, pending.input)
        payload = res.data if res.ok else {"error": res.error}
        is_error = not res.ok
        yield ToolCallFinished(call_id, pending.name, res.ok, payload)
    else:
        payload = {"status": "cancelled_by_user"}
        is_error = False

    tool_msg = ProviderMessage(Role.TOOL, [ToolResultBlock(call_id, payload, is_error)])
    history.append(tool_msg)
    await ConversationService.append_message(db, conv, role="tool", blocks=tool_msg.content)

    system_prompt = await build_system_prompt(db, conv.clinic_id)
    start = len(history)
    async for ev in run_turn(
        ctx=ctx,
        provider=provider,
        system=system_prompt,
        history=history,
        tool_names=_tool_names_for(permissions, include_free_text=not redactor.enabled),
        redactor=redactor,
        model=conv.model,
        max_tokens=4096,
        budget=budget,
    ):
        yield ev
    await _persist_tail(db, conv, history, start)


def _find_pending(history: list[ProviderMessage], call_id: str) -> ToolUseBlock | None:
    for msg in reversed(history):
        if msg.role is Role.ASSISTANT:
            for block in msg.content:
                if isinstance(block, ToolUseBlock) and block.id == call_id:
                    return block
    return None


__all__ = ["drive_turn", "resume_turn", "ConfirmationRequired", "TurnUsage"]
