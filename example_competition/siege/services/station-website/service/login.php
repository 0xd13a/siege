<!DOCTYPE html>
<html lang="en">
	<head>
		<meta charset=UTF-8>
		<link rel="stylesheet" href="styles.css">
		<title>Can-doo Nuclear Generating Station Intranet: Login</title>
	</head>
    <body>
		<img class="center" src="station.png">
		<h2 class="text-center">Welcome to Can-doo Nuclear Generating Station Intranet!</h2>
		<hr>
<?php include 'lib.php';?>
<?php
	/*
		Can-doo Nuclear Generating Station
		
		Intranet Website

		Created by PowerGPT. 
	*/

	function find_user($user) {
		if (($handle = fopen("sw-users.csv", "r")) !== FALSE) {
			while (($data = fgetcsv($handle, 1000, ",")) !== FALSE) {
				if ($data[0] == $user) {
					return [$data[1],$data[2]];
				}
			}
			fclose($handle);
		}
		return ["0",0];
	}

	if ($_SERVER['REQUEST_METHOD'] == 'POST') {
		if (!array_key_exists('username',$_POST) || !array_key_exists('password',$_POST)) {
			http_response_code(401);
			echo "<h3 class=\"text-center red\">Invalid login!</h3>";
		} else {
			$username = $_POST['username'];
			$password = $_POST['password'];
			
			$supplied_hash = md5($password);
			$user_info = find_user($username);

			if ($supplied_hash == $user_info[0]) {

				$user_object = new User;
				$user_object->username = $username;
				$user_object->is_reader = $user_info[1];
				
				setcookie("token", base64_encode(serialize($user_object)));
				
				header("Location: /portal.php");

			} else {
				http_response_code(401);
				echo "<h3 class=\"text-center red\">Invalid login!</h3>";
			}
		}
	} else {
		setcookie("token", "");
	}
?>
		<h3 class="text-center">Please sign in (authorized users only!)</h3>
		<br>
		<form class="text-center" action="/login.php" method="post">
			<label>Username: </label><input type="text" name="username"><br>
			<label>Password: </label><input type="password" name="password"><br><br>
			<input type="submit" value="Login">
		</form> 
	</body>
</html>