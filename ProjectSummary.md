PyAfipWs contains modules to access web services regarding AFIP (Argentina's IRS), related to electronic invoice generation and authorization.

Consists in python modules (using openssl & httplib2), a Windows COM interface compatible with other programming languages (VB, VFP, Delphi, PHP, etc.), command line tools and custom support for web services, xml and pdf.

Additionally includes PyRece, a GUI complete reference implementation that reads invoices from simple CSV files, calls webservices to request authorization, generates PDF and sends it via email (enhanced, free and open source, multiplatform alternative to AFIP's SIAP RECE application)

Web services supported so far:
  * WSAA: authorization & authentication, including digital cryptographic signature
  * WSFE and [WSFEv1](WSFEv1.md): domestic market (electronic invoice)
  * WSBFE: tax bonus (electronic invoice)
  * [WSFEX](WSFEX.md) and WSFEXv1: foreign trade (electronic invoice)
  * WSCTG: agriculture (grain traceability code)
  * WSLPG: agriculture (grain liquidation - invoice)
  * wDigDepFiel: customs (faithful depositary)
  * WSCOC: currency exchange operations autorization
  * COT ARBA: Provincial Operation Transport Code (aka electronic Shipping note)
  * TrazaMed ANMAT: National Medical Drug Traceability Program

More information in [Python Argentina Magazine](http://revista.python.org.ar/2/en/html/pyafip.html) article.