function handle_signup(role) {
    const heading = document.getElementById("heading");
    if (role == "influencer") {
        heading.innerHTML = "Influencer";
        document.getElementById("sponsor").style.display = "none";
        document.getElementById("influencer").style.display = "block";
    } else {
        heading.innerHTML = "Sponsor";
        document.getElementById("influencer").style.display = "none";
        document.getElementById("sponsor").style.display = "block";
    }
}

function validate() {
    let role = document.getElementById("role").value;

    let full_name = document.getElementById("full_name").value;
    let niche = document.getElementById("niche").value;

    let company_name = document.getElementById("company_name").value;
    let industry = document.getElementById("industry").value;

    let username = document.getElementById("username").value;
    let password = document.getElementById("password").value;
    let cpassword = document.getElementById("cpassword").value;
    
    const messages = document.getElementById("js_messages");

    let message = "Please fill out all the fields !";

    if (role == "influencer") {
        if (full_name == "" || niche == "") {
            messages.style.display = "block";
            messages.innerHTML = `<div class="alert alert-danger alert-dismissible fade show fixed-top" role="alert">
                                    ${message}
                                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                                  </div>`
            return false;
        }
    } else {
        if (company_name == "" || industry == "") {
            messages.style.display = "block";
            messages.innerHTML = `<div class="alert alert-danger alert-dismissible fade show fixed-top" role="alert">
                                    ${message}
                                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                                  </div>`
            return false;
        }
    }

    if (username.length < 4) {
        messages.style.display = "block";
        message = "Username should have atleast 4 characters !";
        messages.innerHTML = `<div class="alert alert-danger alert-dismissible fade show fixed-top" role="alert">
                                ${message}
                                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                              </div>`
        return false;
    }

    if (password != cpassword) {
        messages.style.display = "block";
        message = "Passwords do not match !";
        messages.innerHTML = `<div class="alert alert-danger alert-dismissible fade show fixed-top" role="alert">
                                ${message}
                                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                              </div>`
        return false;
    }

    return true;
}