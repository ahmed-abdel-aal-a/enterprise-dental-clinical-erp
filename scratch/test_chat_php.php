<?php
// Simulate HTTP POST request to chat.php
$_SERVER['REQUEST_METHOD'] = 'POST';

// Mock php://input by defining input stream wrapper or creating stream
$postData = json_encode([
    'prompt' => 'ما هي أعراض التهاب عصب السن باختصار؟',
    'model' => 'allam-2-7b'
], JSON_UNESCAPED_UNICODE);

// Use temporary file or stream to feed php://input in CLI
$temp = fopen('php://temp', 'r+');
fwrite($temp, $postData);
rewind($temp);

// In CLI, file_get_contents('php://input') reads from standard input
// Let's test calling chat.php directly via piping stdin or cURL
echo "Ready to test with stdin\n";
