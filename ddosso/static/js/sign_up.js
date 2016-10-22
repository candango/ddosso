$(document).ready(function () {
    var location_root = document.location.pathname.replace("sign_up", "");
    console.debug( "GET " + location_root + "captcha/{id}");
    SignupModel = can.Model.extend({
        findOne: "GET " + location_root + "captcha/{id}",
        create : "POST " + location_root + "sign_up"
    },{});

    var SignupForm = can.Component.extend({
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
                SignupModel.findOne({id: "sign_up"}, function(response) {
                    viewModel.attr("captchaData", response.captcha);
                });
            },
            processLogin: function(login) {
                window.location = login.next_url;
            },
            processLoginError: function(response) {
                $("#signup_captcha").val("")
                var errors = response.responseJSON.errors;
                var errorMessage = '';
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
                    this.viewModel.attr("usernameError",
                        this.viewModel.attr("CAPTCHA_IS_EMPTY"));
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
        init: function() {
            this.on(document, 'ready', function (ev) {

            });
            /**/
        },
        events: {
            "inserted": function () {
                this.viewModel.refreshCaptcha();
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
                    values._xsrf = getCookie('_xsrf');

                    this.viewModel.signup.attr(values).save(
                        this.viewModel.processLogin.bind(this),
                        this.viewModel.processLoginError.bind(this)
                    );
                }
            },
            "#login_form submit": function(event) {
                return false;
            }
        }
    });

    can.extend(SignupForm.prototype, can.event);

    $("#ddosso_sign_up_form").html(can.stache("<sign-up-form></sign-up-form>")());
});