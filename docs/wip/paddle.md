---
exclude: yes
hide:
  - navigation
  - toc
---

<link rel="stylesheet" href="/stylesheets/order.css">
<script src="https://cdn.paddle.com/paddle/paddle.js"></script>

# SysReptor Professional

<div class="checkout-container" id="checkout-container"></div>
  <form id="pre-checkout">
    <div>
      <label for="saas" unselectable>On Premise</label>
      <label class="switch">
        <input type="checkbox" id="saas" checked>
        <span class="slider round"></span>
      </label>
      <label for="saas" unselectable>SaaS</label>
      <br>
    </div>
    
    <label for="users" id="users_label">Users</label>
    <input id="users" type="number"><br>

    <div>
      <span id="price">60</span> EUR per month (charged yearly)
    </div>

    <input id="useremail" type="text" placeholder="Email address"><br>
    <select name="country" id="country"></select><br>

    <input id="postcode" type="text" placeholder="ZIP/Postcode" style="display:none;"><br>
    <div>
      <input type="checkbox" id="tos" name="tos">
      <label for="tos" id="tos_label">I am a business client and accept the Terms of Service</label>
    </div>
  </form>
  [:octicons-credit-card-16: To Payment](#!){ .md-button id="buy" }
</div>

<script type="text/javascript">
  add_countries();
  Paddle.Setup({ vendor: 9630 });
  Paddle.Environment.set('sandbox');
  
  function open_checkout() {
    var tos = document.getElementById("tos");
    if (tos.checked != true) {
      document.getElementById("tos_label").style.color = "crimson";
      return;
    }
    var container = document.getElementById("checkout-container");
    container.innerHTML = '';
    var form = document.getElementById('pre-checkout');
    Paddle.Checkout.open({
      method: 'inline', // set to `inline`
      product: 41490, // replace with a product ID or plan ID
      email: form.useremail.value,
      country: form.country.value,
      postcode: form.postcode.value,
      quantity: form.users.value,
      passthrough: '{tos_accepted: tos.checked, saas: document.getElementById(\'saas\').checked}',
      allowQuantity: true,
      disableLogout: true,
      frameTarget: 'checkout-container', // className of your checkout <div>
      frameInitialHeight: 450, //
      frameStyle: 'width:100%; min-width:312px; background-color: transparent; border: none;' // `min-width` must be set to `286px` or above with checkout padding off; `312px` with checkout padding on.
    });
  }
  document.getElementById('buy').addEventListener('click', open_checkout, false);

  var users = document.getElementById("users");
  var price = document.getElementById("price");
  function update_price() {
    var users_number = parseInt(users.value);
    if (!(Number.isInteger(users_number)) || users_number < 1) {
      users.value = 1;
      users_number = 1;
    }
    price.innerText = users_number*50;
  }
  update_price();
  users.onchange = update_price;

  var select = document.getElementById("country");
  zip_required = ["AU","CA","FR","DE","IN","IT","NL","ES","GB","US"]
  select.onchange=function(){
    if(zip_required.indexOf(select.value)>-1){
      document.getElementById("postcode").style.display="inline";
    }else{
      document.getElementById("postcode").style.display="none";
    }
  }
  function add_countries() {
    html = "";
    obj_fav = {
      "Austria": "AT",
      "Germany": "DE",
      "Australia": "AU",
      "France": "FR",
      "Netherlands": "NL",
      "Spain": "ES",
      "Switzerland": "CH",
      "United Kingdom": "GB",
      "United States": "US",
    }
    obj = {
      "Aland Islands": "AX",
      "Albania": "AL",
      "Algeria": "DZ",
      "American Samoa": "AS",
      "Andorra": "AD",
      "Angola": "AO",
      "Anguilla": "AI",
      "Antigua and Barbuda": "AG",
      "Argentina": "AR",
      "Armenia": "AM",
      "Aruba": "AW",
      "Azerbaijan": "AZ",
      "Bahamas": "BS",
      "Bahrain": "BH",
      "Bangladesh": "BD",
      "Barbados": "BB",
      "Belgium": "BE",
      "Belize": "BZ",
      "Benin": "BJ",
      "Bermuda": "BM",
      "Bhutan": "BT",
      "Bolivia": "BO",
      "Bonaire, Sint Eustatius and Saba": "BQ",
      "Bosnia and Herzegovina": "BA",
      "Botswana": "BW",
      "Bouvet Island": "BV",
      "Brazil": "BR",
      "Brit. Indian Ocean": "IO",
      "British Virgin Islands": "VG",
      "Brunei": "BN",
      "Bulgaria": "BG",
      "Burkina Faso": "BF",
      "Cambodia": "KH",
      "Cameroon": "CM",
      "Canada": "CA",
      "Cape Verde": "CV",
      "Cayman Islands": "KY",
      "Chad": "TD",
      "Chile": "CL",
      "China": "CN",
      "Christmas Island": "CX",
      "Cocos Islands": "CC",
      "Colombia": "CO",
      "Comoros": "KM",
      "Cook Islands": "CK",
      "Costa Rica": "CR",
      "Cote D’Ivoire": "CI",
      "Croatia": "HR",
      "Curaçao": "CW",
      "Cyprus": "CY",
      "Czech Republic": "CZ",
      "Denmark": "DK",
      "Djibouti": "DJ",
      "Dominica": "DM",
      "Dominican Republic": "DO",
      "Ecuador": "EC",
      "Egypt": "EG",
      "El Salvador": "SV",
      "Equatorial Guinea": "GQ",
      "Eritrea": "ER",
      "Estonia": "EE",
      "Ethiopia": "ET",
      "Falkland Islands": "FK",
      "Faroe Islands": "FO",
      "Fiji": "FJ",
      "Finland": "FI",
      "French Guiana": "GF",
      "French Polynesia": "PF",
      "French Southern Terr.": "TF",
      "Gabon": "GA",
      "Gambia": "GM",
      "Georgia": "GE",
      "Ghana": "GH",
      "Gibraltar": "GI",
      "Greece": "GR",
      "Greenland": "GL",
      "Grenada": "GD",
      "Guadeloupe": "GP",
      "Guam": "GU",
      "Guatemala": "GT",
      "Guernsey": "GG",
      "Guinea": "GN",
      "Guinea-Bissau": "GW",
      "Guyana": "GY",
      "Haiti": "HT",
      "Heard/ Mcdonald Islands": "HM",
      "Holy See/ Vatican City": "VA",
      "Honduras": "HN",
      "Hong Kong": "HK",
      "Hungary": "HU",
      "Iceland": "IS",
      "India": "IN",
      "Indonesia": "ID",
      "Ireland": "IE",
      "Isle of Man": "IM",
      "Israel": "IL",
      "Italy": "IT",
      "Jamaica": "JM",
      "Japan": "JP",
      "Jersey": "JE",
      "Jordan": "JO",
      "Kazakhstan": "KZ",
      "Kenya": "KE",
      "Kiribati": "KI",
      "Kosovo": "XK",
      "Kuwait": "KW",
      "Kyrgyzstan": "KG",
      "Lao People’s DR": "LA",
      "Latvia": "LV",
      "Lesotho": "LS",
      "Liechtenstein": "LI",
      "Lithuania": "LT",
      "Luxembourg": "LU",
      "Macao": "MO",
      "Macedonia": "MK",
      "Madagascar": "MG",
      "Malawi": "MW",
      "Malaysia": "MY",
      "Maldives": "MV",
      "Mali": "ML",
      "Malta": "MT",
      "Marshall Islands": "MH",
      "Martinique": "MQ",
      "Mauritania": "MR",
      "Mauritius": "MU",
      "Mayotte": "YT",
      "Mexico": "MX",
      "Micronesia": "FM",
      "Moldova": "MD",
      "Monaco": "MC",
      "Mongolia": "MN",
      "Montenegro": "ME",
      "Montserrat": "MS",
      "Morocco": "MA",
      "Mozambique": "MZ",
      "Namibia": "NA",
      "Nauru": "NR",
      "Nepal": "NP",
      "Netherlands Antilles": "AN",
      "New Caledonia": "NC",
      "New Zealand": "NZ",
      "Niger": "NE",
      "Nigeria": "NG",
      "Niue": "NU",
      "Norfolk Island": "NF",
      "Northern Mariana Islands": "MP",
      "Norway": "NO",
      "Oman": "OM",
      "Pakistan": "PK",
      "Palau": "PW",
      "Palestinian Territory": "PS",
      "Panama": "PA",
      "Papua New Guinea": "PG",
      "Paraguay": "PY",
      "Peru": "PE",
      "Philippines": "PH",
      "Pitcairn": "PN",
      "Poland": "PL",
      "Portugal": "PT",
      "Puerto Rico": "PR",
      "Qatar": "QA",
      "Republic of Serbia": "RS",
      "Reunion": "RE",
      "Romania": "RO",
      "Rwanda": "RW",
      "S. Georgia/ Sandwich Islands": "GS",
      "Saint Helena": "SH",
      "Saint Kitts and Nevis": "KN",
      "Saint Lucia": "LC",
      "Saint Martin": "MF",
      "Saint Pierre and Miquelon": "PM",
      "Saint Vincent/ Grenadines": "VC",
      "Samoa": "WS",
      "San Marino": "SM",
      "Sao Tome and Principe": "ST",
      "Saudi Arabia": "SA",
      "Senegal": "SN",
      "Seychelles": "SC",
      "Singapore": "SG",
      "Slovakia": "SK",
      "Slovenia": "SI",
      "Solomon Islands": "SB",
      "South Africa": "ZA",
      "South Korea": "KR",
      "Sri Lanka": "LK",
      "Sudan": "SD",
      "Suriname": "SR",
      "Svalbard and Jan Mayen": "SJ",
      "Swaziland": "SZ",
      "Sweden": "SE",
      "Taiwan": "TW",
      "Tajikistan": "TJ",
      "Tanzania": "TZ",
      "Thailand": "TH",
      "Timor-Leste": "TL",
      "Togo": "TG",
      "Tokelau": "TK",
      "Tonga": "TO",
      "Trinidad and Tobago": "TT",
      "Tunisia": "TN",
      "Turkey": "TR",
      "Turkmenistan": "TM",
      "Turks and Caicos Islands": "TC",
      "Tuvalu": "TV",
      "U.S. Virgin Islands": "VI",
      "Uganda": "UG",
      "Ukraine": "UA",
      "United Arab Emirates": "AE",
      "United States (M.O.I.)": "UM",
      "Uruguay": "UY",
      "Uzbekistan": "UZ",
      "Vanuatu": "VU",
      "Vietnam": "VN",
      "Wallis and Futuna": "WF",
      "Western Sahara": "EH",
      "Zambia": "ZM"
    }
    html += "<optgroup><option disabled selected value> -- select your country -- </option></optgroup><optgroup>"
    for(var key in obj_fav) {
      html += "<option value=" + obj_fav[key]  + ">" + key + "</option>"
    }
    html += "</optgroup><optgroup>"
    for(var key in obj) {
      html += "<option value=" + obj[key]  + ">" + key + "</option>"
    }
    html += "</optgroup>"
    document.getElementById("country").innerHTML = html;
  }
</script>
