$(function(){

	let error_name = false;
	let error_password = false;
	let error_check_password = false;
	let error_email = false;
	let error_check = false;
	
	let $username = $('#username');
	let $password = $('#password');
	let $confirm_pwd = $('#confirm_pwd');
	let $email = $('#email')

	$username.blur(function() {
		check_username();
	});

	$password.blur(function() {
		check_pwd();
	});

	$confirm_pwd.blur(function() {
		check_cpwd();
	});

	$email.blur(function() {
		check_email();
	});

	$('#allow').click(function() {
		if($(this).is(':checked')) {
			error_check = false;
			$(this).siblings('span').hide();
		} else {
			error_check = true;
			$(this).siblings('span').html('请勾选同意');
			$(this).siblings('span').show();
		}
	});

	function check_username(){
		let len = $username.val().length;
		if(len<5||len>20) {
			$username.next().html('请输入5-20个字符的用户名')
			$username.next().show();
			error_name = true;
		} else {
			$username.next().hide();
			error_name = false;
		}
	}

	function check_pwd(){
		let len = $password.val().length;
		if(len<8||len>20) {
			$password.next().html('密码最少8位，最长20位')
			$password.next().show();
			error_password = true;
		} else {
			$('#pwd').next().hide();
			error_password = false;
		}		
	}


	function check_cpwd(){
		let pass = $confirm_pwd.val();
		let cpass = $confirm_pwd.val();

		if(pass !== cpass) {
			$confirm_pwd.next().html('两次输入的密码不一致')
			$confirm_pwd.next().show();
			error_check_password = true;
		} else {
			$confirm_pwd.next().hide();
			error_check_password = false;
		}		
		
	}

	function check_email(){
		let re = /^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$/;
		if(re.test($email.val())) {
			$email.next().hide();
			error_email = false;
		} else {
			$email.next().html('你输入的邮箱格式不正确')
			$email.next().show();
			error_check_password = true;
		}
	}


	$('#reg_form').submit(function() {
		check_username();
		check_pwd();
		check_cpwd();
		check_email();

		return error_name === false && error_password === false && error_check_password === false && error_email === false && error_check === false;
	});

})