$(document).ready(function () {
    var location_root = document.location.pathname.replace("sign_up", "");

    SignupModel = can.Model.extend({
        findOne: "POST " + location_root + "captcha/{id}",
        create : "POST " + location_root + "sign_up"
    },{});
    SocialModel = can.Model.extend({
        findOne: "POST " + location_root + "sign_up/social"
    },{});

    can.Component.extend({
        tag: "sign-up-form",
        template: can.view("#sign_up_form"),
        viewModel:{
            captchaData: "",
            error: false,
            CAPTCHA_IS_EMPTY: "Informe o valor da imagem.",
            postContainerFocus: false,
            errorMessage: "",
            hasCaptchaError: false,
            hasEmailError: false,
            hasPasswordConfError: false,
            hasPasswordError: false,
            hasUsernameError: false,
            captchaError: "",
            emailError: "",
            passwordError: "",
            passwordConfError: "",
            usernameError: "",
            blurTimeout: null,
            signup: new SignupModel(),
            refreshCaptcha: function() {
                var viewModel = this;
                var values = {id: "sign_up"}
                values._xsrf = get_xsrf();
                SignupModel.findOne(values, function(response) {
                    viewModel.attr("captchaData", response.captcha);
                });
            },
            updateSocial: function() {
                var viewModel = this;
                var values = {}
                values._xsrf = get_xsrf();
                SocialModel.findOne(values, function(response) {
                    console.debug(response);
                });
            },
            processLogin: function(login) {
                window.location = login.next_url;
            },
            processLoginError: function(response) {
                $("#signup_captcha").val("")
                var errors = response.responseJSON.errors;
                var errorMessage = '';
                if(errors.hasOwnProperty('captcha')) {
                    this.viewModel.attr("hasCaptchaError", true);
                    this.viewModel.attr("captchaError", errors.captcha);
                }
                if(errors.hasOwnProperty('email')) {
                    this.viewModel.attr("hasEmailError", true);
                    this.viewModel.attr("emailError", errors.email);
                }
                if(errors.hasOwnProperty('password')) {
                    this.viewModel.attr("hasPasswordError", true);
                    this.viewModel.attr("passwordError", errors.password);
                }
                if(errors.hasOwnProperty('passwordConf')) {
                    this.viewModel.attr("hasPasswordConfError", true);
                    this.viewModel.attr("passwordConfError",
                        errors.passwordConf);
                }
                if(errors.hasOwnProperty('username')) {
                    this.viewModel.attr("hasUsernameError", true);
                    this.viewModel.attr("usernameError", errors.username);
                }
                var errors = new can.Map(response.responseJSON.errors);
                errors.each(
                    function(element, index, list) {
                        if(!this.viewModel.attr('error')){
                            this.viewModel.attr('error', true);
                        }
                        errorMessage += element[0] + '<br>';
                    }.bind(this)
                );
                this.viewModel.attr('errorMessage', errorMessage);
                this.viewModel.refreshCaptcha();
            }
        },
        events: {
            "inserted": function () {
                this.viewModel.refreshCaptcha();
                this.viewModel.updateSocial();
            },
            "#login_button click": function() {
                //this.viewModel.attr('error', false);
                //this.viewModel.attr('errorMessage', '');
                this.viewModel.attr("hasCaptchaError", false);
                this.viewModel.attr("captchaError", "");

                if(!($("#signup_captcha").val())){
                    this.viewModel.attr("hasCaptchaError", true);
                    this.viewModel.attr("captchaError",
                        this.viewModel.attr("CAPTCHA_IS_EMPTY"));
                } else {
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
                    this.viewModel.signup.attr(values).save(
                        this.viewModel.processLogin.bind(this),
                        this.viewModel.processLoginError.bind(this)
                    );
                }
            },
            "#refresh_captcha click": function(event) {
                this.viewModel.refreshCaptcha();
            },
            "#signinLink click": function(event) {
                window.document.location = location_root + "sign_in";
            },
            "#login_form submit": function(event) {
                return false;
            }
        }
    });

    $("#ddosso_sign_up_form").html(can.stache("<sign-up-form></sign-up-form>")());
});
