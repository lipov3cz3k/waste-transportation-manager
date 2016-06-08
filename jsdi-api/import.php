<?php
// Log access ip
$logFile = "access.log";
$logLine = date('Y-m-d H:i:s') . " - $_SERVER[REMOTE_ADDR] ";

//check today's dir
$today = date('Y-m-d');
if (!file_exists("data/".$today))
    mkdir("data/".$today, 0700, true);
$out_dir = "data/".$today;

//save POST to xml file
$fileName = $today . ".xml";
$data = file_get_contents_utf8("php://input");
$filePath = file_newname($out_dir, $fileName);
if($data != null)
{
  file_put_contents($filePath, $data);
  $logLine .= $filePath;
}
else
{
  echo "Missing payload";
  $logLine .= "Missing payload";
}

// Save log to file
file_put_contents($logFile, $logLine . PHP_EOL, FILE_APPEND);



function file_newname($path, $filename){
    if ($pos = strrpos($filename, '.')) {
           $name = substr($filename, 0, $pos);
           $ext = substr($filename, $pos);
    } else {
           $name = $filename;
           $ext = "";
    }

    $newpath = $path.'/'.$filename;
    $newname = $filename;
    $counter = 0;
    do {
           $newname = $name .'_'. sprintf("%04d", $counter) . $ext;
           $newpath = $path.'/'.$newname;
           $counter++;
    }while (file_exists($newpath));

    return $newpath;
}

function file_get_contents_utf8($fn) {
     $content = file_get_contents($fn);
      return mb_convert_encoding($content, 'UTF-8',
          mb_detect_encoding($content, 'UTF-8, ISO-8859-1', true));
}

?>