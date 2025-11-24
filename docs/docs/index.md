---
title: SysReptor Pentest Report Creator
---

<div style="background-color: black; color: white; text-align: center; padding: 1em; margin-bottom:0; position: relative; overflow: visible;">
  <div style="display: flex; justify-content: space-between;">
    <div style="flex: 1; padding: 1em; ">
      <h1 style="color: white; font-weight: bold; font-size: 3em">BLACK<br>FRIDAY<br>-30%</h1>
      <p style="font-size: 1.2em; margin: 0.5em 0 0 0;">Code: <strong>BLACKFRIDAY2025</strong></p>
      <p style="font-size: 0.75em; margin-top: 0.2em;">Valid for new customers.</p>
      
      <a class="black-friday-button" style="text-align:center; margin-top:1.5em;" href="https://portal.sysreptor.com/order/" target="_blank">Order Now</a>
      <p id="countdown" style="font-size: 1em; font-weight: bold;"></p>
      
      <script>
        function updateCountdown() {
          const targetDate = new Date('November 30, 2025 23:59:59 GMT');
          const now = new Date();
          const difference = targetDate - now;

          const days = Math.max(0, Math.floor(difference / (1000 * 60 * 60 * 24))+1);
          document.getElementById('countdown').innerHTML = `${days} ${days > 1 ? 'days' : 'day'} to go`;
        }
        updateCountdown();
      </script>
    </div>
    <div style="flex: 1; padding: 1em; position: relative;">
      <img 
        style="display: block; 
            margin-left: auto;
            margin-right: auto;
            width: 45.5em;
            height: auto;
            position: relative;
            bottom: -5em;"
        src="/assets/dino/eating_cake.svg"
        alt="It's a pie. Because Pentest reports are as easy as pie.">
  </img>
    </div>
  </div>
</div>
<div style="margin-top: 7em;"></div>


<!--
<h1 style="text-align: center;font-weight:bold;">Pentest Reports<br>Easy As Pie.</h1>

<div style="overflow: hidden;">
  <img 
      style="display: block; 
            margin-left: auto;
            margin-right: auto;
            margin-bottom: -5.3em;
            width: 10em;"
      src="/assets/dino/eating_cake.svg"
      viewBox="0 0 200 200"
      height="200"
      width="130"
      alt="It's a pie. Because Pentest reports are as easy as pie.">
  </img>
</div>-->

<div class="grid cards" style="text-align: center; margin-top: 0;" markdown>

-   __Customize Reports__

    <img 
        style="display: block; 
              margin-left: auto;
              margin-right: auto;"
        src="/assets/emojis/wood.svg"
        viewBox="0 0 50 50"
        height="50"
        width="50"
        alt="A piece of wood. It's easy to fall off.">
    </img>

    Design in HTML.

    As easy as falling off a log.


-   __Write Reports__

    <img 
        style="display: block; 
              margin-left: auto;
              margin-right: auto;"
        src="/assets/emojis/bicycle.svg"
        viewBox="0 0 50 50"
        height="50"
        width="50"
        alt="A bicycle. It gives you an easy ride.">
    </img>

    Write in Markdown.

    It gives you an easy ride.

-   __Render and Download__

    <img 
        style="display: block; 
              margin-left: auto;
              margin-right: auto;"
        src="/assets/emojis/flexed-biceps.svg"
        viewBox="0 0 50 50"
        height="50"
        width="50"
        alt="A flexed biceps. Render and download are so easy.">
    </img>
 
    Render to PDF.

    Easier done than said.

-   __Operate Platform__

    <img 
        style="display: block; 
              margin-left: auto;
              margin-right: auto;"
        src="/assets/emojis/lemon.svg"
        viewBox="0 0 50 50"
        height="50"
        width="50"
        alt="A lemon. It's as easy as squeezing a lemon.">
    </img>

    Self-Hosted or Cloud.

    Easy peasy lemon squeezy.

</div>

<br><div style="text-align:center">[:fire: Get Started](setup/installation.md){ .md-button target="_blank" }</div>
<br><div style="text-align:center">[:sauropod: Book a Demo](https://outlook.office365.com/book/SysReptorDemo@syslifters.com/s/gUjy2xF2GEeSc_6mDLvvkA2){ .md-button target="_blank" }</div>

<br>
<figure markdown>
  ![Create finding from template](images/create_finding_from_template.gif)
  <figcaption>Create finding from template</figcaption>
</figure>

<figure markdown>
  ![Export report as PDF](images/export_project.gif)
  <figcaption>Export report as PDF</figcaption>
</figure>
