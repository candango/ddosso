$(document).ready(function () {
    var location_root = document.location.pathname.replace("sign_in", "");

    SigninModel = can.Model.extend({
        create : "POST " + location_root + "sign_in"
    },{});

    can.Component.extend({
        tag: "sign-in-form",
        template: can.view("#sign_in_form"),
        viewModel:{
            hasError: false,
            postContainerFocus: false,
            errorMessage: "",
            hasPasswordError: false,
            hasUsernameError: false,
            passwordError: "",
            usernameError: "",
            blurTimeout: null,
            signin: new SigninModel(),
            processLogin: function(login) {
                console.debug(login);
                window.location = login.next_url;
            },
            processLoginError: function(response) {
                var errors = response.responseJSON.errors;
                var errorMessage = '';
                if(errors.hasOwnProperty('password')) {
                    this.viewModel.attr("hasPasswordError", true);
                    this.viewModel.attr("passwordError", errors.password);
                }
                if(errors.hasOwnProperty('username')) {
                    this.viewModel.attr("hasUsernameError", true);
                    this.viewModel.attr("usernameError", errors.username);
                }
                if(errors.hasOwnProperty('form')) {
                    this.viewModel.attr("hasError", true);
                    this.viewModel.attr("errorMessage", errors.form);
                }
            }
        },
        events: {
            "#signinButton click": function() {
                //this.viewModel.attr('error', false);
                //this.viewModel.attr('errorMessage', '');
                this.viewModel.attr("hasError", false);
                this.viewModel.attr("hasEmailError", false);
                this.viewModel.attr("hasPasswordError", false);
                this.viewModel.attr("hasPasswordConfError", false);
                this.viewModel.attr("hasUsernameError", false);
                this.viewModel.attr('emailError', "");
                this.viewModel.attr('passwordError', "");
                this.viewModel.attr('passwordConfError', "");
                this.viewModel.attr("usernameError", "");

                var form = this.element.find('form');
                var values = can.deparam(form.serialize());
                var parameters = [];
                values._xsrf = get_xsrf();
                this.viewModel.signin.attr(values).save(
                    this.viewModel.processLogin.bind(this),
                    this.viewModel.processLoginError.bind(this)
                );
            },
            "#signinForm submit": function(event) {
                return false;
            },
            "#signupLink click": function(event) {
                window.document.location = location_root + "sign_up";
            }
        }
    });

    $("#ddosso_sign_in_form").html(
        can.stache("<sign-in-form></sign-in-form>")());
});
