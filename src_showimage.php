<?php
// header("Content-Length: 1" /*. filesize($name)*/);
if( isset($_GET["file"]) && !isset($_GET["size"]) ){
        // open the file in a binary mode
        header("Content-Type: image/jpeg");
        $name = $_GET["file"];

		// restrict urls
        if (filter_var($name, FILTER_VALIDATE_URL)) {
        	exit();
        }

        $fp = fopen($name, 'rb');

        // send the right headers
        header("Content-Type: image/jpeg");

        // dump the picture and stop the script
        fpassthru($fp);
        exit;
}
elseif (isset($_GET["file"]) && isset($_GET["size"])){
        header("Content-Type: image/jpeg");
        $name = $_GET["file"];
        
        // restrict urls
        if (filter_var($name, FILTER_VALIDATE_URL)) {
        	exit();
        }
                
        $fp = fopen($name, 'rb');

        // send the right headers
        header("Content-Type: image/jpeg");

        // dump the picture and stop the script
        fpassthru($fp);
        exit;
}
?>
