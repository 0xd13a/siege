<!DOCTYPE html>
<html lang="en">
	<head>
		<meta charset=UTF-8>
		<link rel="stylesheet" href="styles.css">
		<title>Can-doo Nuclear Generating Station Intranet: Portal</title>
	</head>
    <body>
		<img class="center" src="/station.png">
		<?php include 'lib.php';?>
		<?php 
			/*
				Can-doo Nuclear Generating Station
			
				Intranet Website

				Created by PowerGPT. 
			*/
			error_reporting(E_ALL);
			$file_name = '/tmp/news.txt';
			
			$token = "";
			if (array_key_exists("token",$_COOKIE)) {
				$token = $_COOKIE["token"];	
			}
						
			if ($token == "") {
				header("Location: /login.php");
			}
			$user_obj = unserialize(base64_decode($token));
						
			echo "<span class=\"text-right\"><span class=\"bold\">Welcome $user_obj->username!</span>&nbsp;<a href=\"/login.php\">Logout</a></span>";

		?>
		
		<h2 class="text-center">Can-doo Nuclear Generating Station Intranet</h2>
		<hr>
		<br>
		<table>
			<tr><td><img src="reactor.jpg"/></td>
			<td style="width: 40%;">
			<?php
				if (($_SERVER['REQUEST_METHOD'] == 'POST') && array_key_exists('contents',$_POST) && ($user_obj->is_reader != 1)) {
					$contents = $_POST['contents'];
					if (str_contains($contents, "hack")) {
						echo "<h3 class=\"text-center red\">You can't post dangerous content!</h3>";
					} else {
						$i = 0;
						$file = fopen($file_name, 'a');
						fwrite($file, date("Y-m-d h:i:sa") . ',' . base64_encode($contents) . PHP_EOL);
						fclose($file);
					}
				}
			?>
			
			<?php if($user_obj->is_reader != 1) { ?>
				<p>Enter news text to post (do not add any scripting!):</p>
				<form class="text-center" action="/portal.php" method="post">
					<textarea name="contents" rows="4" cols="50"></textarea>
					<input type="submit" value="Post">
				</form> 
			<?php } ?>
			<h3 class="text-center">Station news</h3>
			<div class="scrollable">
			<?php
				$news_arr = [];
				if ((file_exists($file_name)) && 
				    ($handle = fopen($file_name, "r")) !== FALSE) {
					while (($data = fgetcsv($handle, 1000, ",")) !== FALSE) {
						array_unshift($news_arr, "<b>$data[0]</b><br><br>" . base64_decode($data[1]) . "<br><br><br>" . PHP_EOL);
					}
					fclose($handle);
					
					foreach ($news_arr as &$val) {
						echo $val;
					}
				}			
			?>
			</div>
			</td></tr>
		</table>
	</body>
</html>