$(document).ready(function () {
    SignUpModel = can.Model({
        create : "POST /sign_up"
    },{});

    can.Component.extend({
        tag: "sign-up-form",
        template: can.view("#sign_up_form"),
        viewModel:{
            error: false,
            postContainerFocus: false,
            errorMessage: '',
            userNameError: false,
            passwordError: false,
            blurTimeout: null,
            stream_post: new SignUpModel(),
            blurControls: function() {
                var viewModel = this;
                var doBlur = function() {
                    viewModel.attr("postContainerFocus", false);
                }
                this.blurTimeout = window.setTimeout(doBlur, 100);
            },
            processLogin: function(login) {
                window.location = login.next_url;
            },
            processLoginError: function(response) {
                var errorMessage = '';
                if(response.responseJSON.errors.hasOwnProperty('username')) {
                    this.viewModel.attr('userNameError', true);
                }
                if(response.responseJSON.errors.hasOwnProperty('password')) {
                    this.viewModel.attr('passwordError', true);
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
            "#login_button click": function() {
                //this.viewModel.attr('error', false);
                //this.viewModel.attr('errorMessage', '');
                //this.viewModel.attr('userNameError', false);
                //this.viewModel.attr('passwordError', false);

                var form = this.element.find('form');
                //console.log(form.serialize());
                var values = can.deparam(form.serialize());
                var parameters = [];
                console.debug(values);
                //values._xsrf = getCookie('_xsrf');
                /*this.viewModel.login.attr(values).save(
                    this.viewModel.processLogin.bind(this),
                    this.viewModel.processLoginError.bind(this)
                );*/
            },
            "#login_form submit": function(event) {
                return false;
            }
        }
    });
    $("#ddosso_sign_up_form").html(can.stache("<sign-up-form></sign-up-form>")());
});
