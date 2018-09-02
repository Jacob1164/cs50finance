// whole webpage
$(document).ready(function () {

    let parameters = {};

    // this functions gets the current stock prices
    function reload() {
        if (document.URL == "http://ide50-jacob1164.cs50.io:8080/")
        {
            $.getJSON("/update", parameters, function update(data, textStatus, jqXHR) {
                let total = 0;
                for (let i = 0; i < data.length; i++)
                {
                    total = data[i]["total"];
                    actotal = data[i]["bal"];
                    document.getElementById(`${i}`).innerHTML = data[i]["price"];
                    document.getElementById(`${i}`).setAttribute("style", `color: ${data[i]["color"]};`);
                    document.getElementById(`t${i}`).innerHTML = data[i]["tot"];
                }
                document.getElementById("total").innerHTML = total;
                document.getElementById("load").innerHTML = "";

                let color = "white";
                if (actotal < 20000)
                    color = "red";
                else if (actotal == 20000)
                    color = "white";
                else
                    color = "green";

                document.getElementById("page").setAttribute("style", `background-color: ${color};`);

                setTimeout(reload, 20000);

            });
        }
    }


    // color buttons
    $('.button').click(function () {
        $('#page').css('background-color', this.innerHTML.toLowerCase());
    });

    // quote form
    $('#quote').submit(function () {
        if (!$('#quote input[name = symbol]').val())
        {
            alert("missing symbol");
            return false;
        }
        return true;
    });

    // buy form
    $('#buy').submit(function () {
        if (!$('#buy input[name = symbol]').val())
        {
            alert("missing symbol");
            return false;
        }
        if (!$('#buy input[name = shares]').val())
        {
            alert("missing # of shares");
            return false;
        }
        return true;
    });

    // sell form
    $('#sell').submit(function () {
        if (!$('#sell input[name = shares]').val())
        {
            alert("missing # of shares");
            return false;
        }
        return true;
    });

    // login
    $('#login').submit(function () {
        if (!$('#login input[name = username]').val())
        {
            alert("missing username");
            return false;
        }
        if (!$('#login input[name = password]').val())
        {
            alert("missing password");
            return false;
        }
        return true;
    });

    // register
    $('#register').submit(function () {
        if (!$('#register input[name = username]').val())
        {
            alert("missing username");
            return false;
        }
        if (!$('#register input[name = password]').val())
        {
            alert("missing password");
            return false;
        }
        if (!$('#register input[name = confirmation]').val())
        {
            alert("missing confirmation");
            return false;
        }
        if ($('#register input[name = confirmation]').val() != $('#register input[name = password]').val())
        {
            alert("passwords don't match");
            return false;
        }
        return true;
    });

    // account
    $('#account').submit(function () {
        if (!$('#account input[name = old]').val())
        {
            alert("Enter your current password");
            return false;
        }
        if (!$('#account input[name = new]').val())
        {
            alert("Enter your new password");
            return false;
        }
        if (!$('#account input[name = confirm]').val())
        {
            alert("Retype your new password");
            return false;
        }
        if ($('#account input[name = new]').val() != $('#account input[name = confirm]').val())
        {
            alert("passwords don't match");
            return false;
        }
        return true;
    });

    reload();
});