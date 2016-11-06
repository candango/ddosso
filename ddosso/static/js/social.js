$(document).ready(function () {
    var SocialModel = can.Model.extend({
        findOne: "POST " + location_root + "social/{id}",
        destroy: "DELETE " + location_root + "social/{id}"
    },{});

    can.Component.extend({
        tag: "socialControls",
        template: can.view("#socialControlsStache"),
        viewModel: {
            hasCaptchaError: false,
            isAuthenticated: false,
            isFacebookEnabled: false,
            isGoogleEnabled: false,
            isTwitterEnabled: false,
            socialImageClass: "",
            socialType: "",
            socialPicture: "",
            socialFirstName: "",
            socialLastName: "",
            social: new SocialModel(),
            updateSocial: function () {
                var viewModel = this;
                var values = {
                    id: window.location.pathname.replace(location_root, "")
                };
                values._xsrf = get_xsrf();
                SocialModel.findOne(values, function (social) {
                    if (social.authenticated) {
                        viewModel.attr("isAuthenticated", true);
                        viewModel.attr("socialPicture", social.picture);
                        viewModel.attr("socialFirstName", social.first_name);
                        viewModel.attr("socialLastName", social.last_name);
                        viewModel.attr("socialImageClass", social.type);
                        viewModel.attr("socialType", social.type);
                        if($("#userEmail").length) {
                            if(social.type == "google"){
                                viewModel.attr("socialImageClass",
                                    "google-plus");
                                if(!$("#userEmail").val()){
                                    $("#userEmail").val(social.handler);
                                }
                            }
                            if(social.type == "twitter"){
                                if(!$("#username").val()){
                                    $("#username").val(social.handler);
                                }
                            }
                        }
                    }
                    else{
                        viewModel.attr("isAuthenticated", false);
                        viewModel.attr("socialPicture", "");
                        viewModel.attr("socialFirstName", "");
                        viewModel.attr("socialLastName", "");
                        if($("#userEmail").length) {
                            if($("#userEmail").val()){
                                $("#userEmail").val("");
                            }
                        }
                    }
                    if(social.google.enabled) {
                        viewModel.attr("isGoogleEnabled", true);
                    }
                    if(social.twitter.enabled) {
                        viewModel.attr("isTwitterEnabled", true);
                    }
                });
            },
            processReset: function (response) {
                this.viewModel.updateSocial();
                this.viewModel.attr("isAuthenticated", false);
            }
        },
        events: {
            "inserted": function () {
                this.viewModel.updateSocial();
            },
            "#googleOauth click": function() {
                window.document.location = location_root + "google/oauth2";
            },
            "#twitterOauth click": function() {
                window.document.location = location_root + "twitter/oauth";
            },
            "#resetOauth click": function(event) {
                console.debug(event);
                var values = {id: "social"};
                values._xsrf = get_xsrf();
                this.viewModel.social.attr(values).destroy(
                    this.viewModel.processReset.bind(this)
                );
            },
            "#signinLink click": function(event) {
                window.document.location = location_root + "sign_in";
            },
            "#login_form submit": function(event) {
                return false;
            }
        }
    });

    $("#socialControls").html(
        can.stache("<socialControls></socialControls>")());
});
