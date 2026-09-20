<script setup lang="ts">
const model = defineModel<string>({ required: true })
defineProps<{ busy: boolean }>()
const emit = defineEmits<{ submit: [] }>()
const { t } = useI18n()

const isListening = ref(false)
const isSupported = ref(false)
let recognition: any = null
let baseText = ''

onMounted(() => {
  if (typeof window !== 'undefined') {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (SpeechRecognition) {
      isSupported.value = true
      recognition = new SpeechRecognition()
      recognition.continuous = true
      recognition.interimResults = true
      recognition.lang = 'ar-EG'

      recognition.onstart = () => {
        isListening.value = true
        baseText = model.value ? model.value.trim() + ' ' : ''
      }

      recognition.onresult = (event: any) => {
        let interimTranscript = ''
        let finalTranscript = ''

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript
          } else {
            interimTranscript += event.results[i][0].transcript
          }
        }

        const currentSpeech = (finalTranscript || interimTranscript).trim()
        if (currentSpeech) {
          model.value = baseText + currentSpeech
        }
      }

      recognition.onerror = (event: any) => {
        console.warn('Speech recognition error:', event.error)
        isListening.value = false
      }

      recognition.onend = () => {
        isListening.value = false
      }
    }
  }
})

onBeforeUnmount(() => {
  if (recognition && isListening.value) {
    recognition.stop()
  }
})

function toggleListening() {
  if (!recognition) return
  if (isListening.value) {
    recognition.stop()
  } else {
    try {
      recognition.start()
    } catch (err) {
      console.warn('Could not start speech recognition:', err)
    }
  }
}

function onKeydown(e: KeyboardEvent) {
  // Enter sends; Shift+Enter inserts a newline.
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    if (isListening.value && recognition) {
      recognition.stop()
    }
    emit('submit')
  }
}
</script>

<template>
  <div class="border-t border-default pt-2">
    <div class="flex items-end gap-2">
      <UTextarea
        v-model="model"
        :rows="1"
        autoresize
        :placeholder="isListening ? 'جارٍ الاستماع إليك... تحدث الآن' : t('copilot.placeholder')"
        class="flex-1"
        :disabled="busy"
        @keydown="onKeydown"
      />
      <button
        v-if="isSupported"
        type="button"
        @click="toggleListening"
        :class="[
          'p-2 rounded-full transition-colors duration-200 focus:outline-none shrink-0',
          isListening ? 'text-red-600 bg-red-100 animate-pulse' : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
        ]"
        title="تحدث الآن"
      >
        <!-- أيقونة المايكروفون يعمل (أحمر) -->
        <svg v-if="isListening" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 002 0V8a1 1 0 00-1-1zm4 0a1 1 0 00-1 1v4a1 1 0 002 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
        </svg>
        <!-- أيقونة المايكروفون مغلق (رمادي) -->
        <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
        </svg>
      </button>
      <UButton
        icon="i-lucide-send"
        color="primary"
        :loading="busy"
        :disabled="!model.trim()"
        :aria-label="t('copilot.send')"
        @click="emit('submit')"
      />
    </div>
    <p class="mt-1.5 flex items-center justify-center gap-1 text-center text-xs text-muted">
      <UIcon name="i-lucide-shield-check" />
      {{ t('copilot.trust') }}
    </p>
  </div>
</template>
