$(function () {
    var inputUsername = $('input[name="username"]');
    var inputPassword = $('input[name="password"]');
    var inputPasswordConfirm = $('input[name="password_confirm"]');

    var set_normal = function(inputObj) {
        var parent = inputObj.parent();
        parent.removeClass('has-success').removeClass('has-error');
        parent.remove("span");
        inputObj.tooltip('hide');
    };

    var set_success = function(inputObj) {
        var parent = inputObj.parent();
        parent.addClass("has-success");
        parent.append($("span").attr("class", "glyphicon glyphicon-ok form-control-feedback"));
        inputObj.tooltip('hide');
    };

    var set_error = function(inputObj, msg) {
        var parent = inputObj.parent();
        parent.addClass("has-error");
        parent.append($("span").attr("class", "glyphicon glyphicon-remove form-control-feedback"));
        if(msg){
            inputObj.tooltip({"animation":true, "title":msg});
            inputObj.tooltip("show");
        }
    };

    var validate = function(inputObj, func) {
        inputObj.blur(function() {
            func(inputObj);
        });
        inputObj.keydown(function() {
            set_normal(inputObj);
        })
    };

    validate(inputUsername, function() {
        var username = inputUsername.val();
        if(!username) {
            set_error(inputUsername, "Username can not be empty.");
            return;
        }
        $.get('/api/get_username_availability?username=' + username, function (data, status) {
            if(data['availability']) {
                set_success(inputUsername);
            }else {
                set_error(inputUsername, data['reason']);
            }
        });
    });

    validate(inputPassword, function() {
        var password = inputPassword.val();
        if(password) {
            set_success(inputPassword);
        }else {
            set_error(inputPassword, "password can not be empty.");
        }
    });

    validate(inputPasswordConfirm, function() {
        var password = inputPassword.val();
        var passwordConfirm = inputPasswordConfirm.val();
        if(password == passwordConfirm && passwordConfirm) {
            set_success(inputPasswordConfirm);
        }else {
            set_error(inputPasswordConfirm, "password confirm is incorrect.");
        }
    });
});