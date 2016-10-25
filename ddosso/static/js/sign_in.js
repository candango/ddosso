$(document).ready(function () {
    var location_root = document.location.pathname.replace("sign_in", "");

    SigninModel = can.Model.extend({
        create : "POST " + location_root + "sign_in"
    },{});
    SocialModel = can.Model.extend({
        findOne: "POST " + location_root + "sign_up/social",
    },{});

    can.Component.extend({
        tag: "sign-in-form",
        template: can.view("#sign_in_form"),
        viewModel:{
            error: false,
            postContainerFocus: false,
            errorMessage: "",
            hasPasswordError: false,
            hasUsernameError: false,
            passwordError: "",
            usernameError: "",
            blurTimeout: null,
            signin: new SigninModel(),
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
            }
        },
        events: {
            "inserted": function () {
                this.viewModel.updateSocial();
            },
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
            }
        }
    });

    $("#ddosso_sign_in_form").html(
        can.stache("<sign-in-form></sign-in-form>")());
});
