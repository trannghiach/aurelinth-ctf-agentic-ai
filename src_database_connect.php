<?PHP
	$connection = mysql_connect('127.0.0.1', 'acuart', 'trustno1')
		or die('Website is out of order. Please visit back later. Thank you for understanding.');
		
	mysql_select_db('acuart', $connection)
		or die('Website is out of order. Please visit back later. Thank you for understanding.');
?>
