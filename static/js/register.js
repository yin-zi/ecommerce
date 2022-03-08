$(function(){

	let error_name = false;
	let error_password = false;
	let error_check_password = false;
	let error_email = false;
	let error_captcha = false;
	let error_check = false;
	
	let $username = $('#username');
	let $password = $('#password');
	let $confirm_pwd = $('#confirm_pwd');
	let $email = $('#email');
	let $captcha = $('#captcha');
    let $captcha_im = $('#captcha_im');
    let $captcha_uuid = $('#captcha_uuid');

    let captcha_uuid = '';

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

	$captcha.blur(function() {
		check_captcha();
	})

	$('#allow').click(function() {
		if($(this).is(':checked')) {
			error_check = true;
			$(this).siblings('span').hide();
		} else {
			error_check = false;
			$(this).siblings('span').html('请勾选同意');
			$(this).siblings('span').show();
		}
	});

	function check_username(){
		let len = $username.val().length;
		if(len<5||len>20) {
			$username.next().html('请输入5-20个字符的用户名')
			$username.next().show();
			error_name = false;
		} else {
			$username.next().hide();
			error_name = true;
		}
	}

	function check_pwd(){
		let len = $password.val().length;
		if(len<8||len>20) {
			$password.next().html('密码最少8位，最长20位')
			$password.next().show();
			error_password = false;
		} else {
			$password.next().hide();
			error_password = true;
		}
	}

	function check_cpwd(){
		let pass = $password.val();
		let cpass = $confirm_pwd.val();

		if(pass !== cpass) {
			$confirm_pwd.next().html('两次输入的密码不一致')
			$confirm_pwd.next().show();
			error_check_password = false;
		} else {
			$confirm_pwd.next().hide();
			error_check_password = true;
		}		
		
	}

	function check_email(){
		let re = /^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$/;
		if(re.test($email.val())) {
			$email.next().hide();
			error_email = true;
		} else {
			$email.next().html('你输入的邮箱格式不正确');
			$email.next().show();
			error_check_password = false;
		}
	}

	function check_captcha() {
		let len = $captcha.val().length;
		if (len <= 0 || len > 2) {
			error_captcha = false;
			$captcha.next().html('少骗我了，答案肯定不对');
			$captcha.next().show();
		} else {
			$captcha.next().hide()
			error_captcha = true;
		}
	}

    // 表单提交前 初步检查各项参数是否符合要求
	$('#reg_form').submit(function() {
		check_username();
		check_pwd();
		check_cpwd();
		check_email();
		check_captcha();

		return error_name && error_password && error_check_password && error_email && error_captcha;
	});

    // 生成uuid4的函数
    function guid() {
        function S4() {
           return (((1+Math.random())*0x10000)|0).toString(16).substring(1);
        }
        return (S4()+S4()+"-"+S4()+"-"+S4()+"-"+S4()+"-"+S4()+S4()+S4());
    }

	// 图片验证码
    function get_captcha() {
        captcha_uuid = guid();
        $captcha_im.attr("src", "/captcha/" + captcha_uuid);
        $captcha_uuid.val(captcha_uuid);
    }

    // 页面加载完成调用一次 点击验证码图片也刷新
    get_captcha();
    $captcha_im.click(get_captcha);

});