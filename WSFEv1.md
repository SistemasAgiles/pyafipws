Para documentación en español, ver:
http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs (full user manual - documentation)

For information in Spanish see:
http://www.sistemasagiles.com.ar/trac/wiki/ProyectoWSFEv1



# Introduction #

WSFEv1 is the webservice to authorize domestic/local invoices according AFIP (Argentina "IRS") regulations.

This webservice allows to authorize an invoice (i.e. get the CAE: Electronic Autorization Code) so it can be sent to the customer.

Invoice Class:
  * A: sales to Taxpayer
  * B: sales to Final Consumer
  * C: sales of Taxpayer registered into simplified tax scheme "monotributo"

AFIP General Resolutions:
  * RG2485: General Regime
  * RG2975: "Importers"
  * RG2959: Tourism activities
  * RG2904: "Big" Taxpayers notified by administrative judge to send detailed sales information
  * RG2926: CAEA: "Big" Taxpayers that used to self-print their invoices (Electronic Authorization Code "in-advance")
  * RG3067: simplified small taxpayers ("monotributo")

Webservice:
  * Current: WSFEv1 (a.k.a. version 1, version 1.1 and version 2)
  * Previous: WSFE (version 0) available until 30/06/2011

PyAfipWs Interface options:
  * COM Interface (windows only): CreateObject("WSFEv1")
  * Command-line communication tool: RECE1.EXE
  * Python module: wsfev1.py

Current Installer:
  * Stable: [instalador-WSFEV1-1.10d-homo.exe](http://pyafipws.googlecode.com/files/instalador-WSFEV1-1.10d-homo.exe) (recommended)
  * Development: [instalador-WSFEV1-1.12d-homo.exe](http://pyafipws.googlecode.com/files/instalador-WSFEV1-1.12d-homo.exe) (new features)

Installers are for evaluation purposes only (testing - homologation).
For production, consult our [Commercial Support](http://www.sistemasagiles.com.ar) or see InstalacionCodigoFuente (Source Code Installation Instructions)

# Details #

Most modern programming languages in windows support COM Automation  (a.k.a. Component Object Model, ActiveX DLL, similar to OCX controls) via CreateObject or similar function, and this interface exposes WSAA and WSFEv1 objects to be used directly from legacy programs.

Some known supported programming languages so far:
  * Visual Basic Classic (5,6)
  * Visual Basic .Net
  * Visual Basic For Applications (MS Access, MS Excel, et. al.)
  * Visual Fox Pro
  * Delphi
  * ABAP (SAP)
  * Fujitsu NetCobol
  * Powerbuilder
  * X++ (Microsoft Dynamics)
  * Genexus

If your programming language doesn't support COM, the interface has a Command Line Tool called RECE1 to perform invoice authorization using text files or DBF tables (see bellow).

## Visual Basic (5/6) COM Example ##

The following code is a detailed example to explain main features and recommended process and data needed to authorize a valid electronic invoice:

```
' Workflow example COM Interface with new WSFEv1 AFIP webservice
' As of RG2904 Art. 4 Op. B (without detail)
' 2010 (C) Mariano Reingart <reingart@gmail.com>
' License: GPLv3

Sub Main()
    Dim WSAA As Object, WSFEv1 As Object
    
    ' Create interface object to the Authentication webservice
    Set WSAA = CreateObject("WSAA")
    
    ' Generate Access Request Ticket (TRA) for WSFEv1 (same as WSFE)
    tra = WSAA.CreateTRA("wsfe")
    Debug.Print tra
    
    ' Set path to the certificate and private key
    Path = CurDir() + "\"
    ' Certificado: certificate signed by AFIP
    ' ClavePrivada: private key used to generate CSR
    Certificado = "..\..\reingart.crt" ' demo cert, change!
    ClavePrivada = "..\..\reingart.key" ' demo pk, change!
    
    ' Generate Signed Encrypted Message (CMS)
    cms = WSAA.SignTRA(tra, Path + Certificado, Path + ClavePrivada)
    Debug.Print cms
    
    ' Call webservice to get authentication:
    ' (URL for testing, change for production)
    ta = WSAA.CallWSAA(cms, "https://wsaahomo.afip.gov.ar/ws/services/LoginCms")

    ' Print Access Ticket (TA) containing Token and Sign
    Debug.Print ta
    Debug.Print "Token:", WSAA.Token
    Debug.Print "Sign:", WSAA.Sign
    
    ' Once obtained, token and sign can be used for 12 hours
    ' (this time lapse can be changed, see TTL parameter at CreateTRA)
    
    ' Create interface object to Electronic Invoice webservice
    ' (note WSFEv1 instead of WSFE)
    Set WSFEv1 = CreateObject("WSFEv1")
    Debug.Print WSFEv1.version
    
    ' Set authentication token and sign to be used at WSFE (from WSAA)
    WSFEv1.Token = WSAA.Token
    WSFEv1.Sign = WSAA.Sign
    
    ' Issuer CUIT (must be registered to the certificate at AFIP)
    WSFEv1.Cuit = "20267565393"
    
    ' Connect to WSFEv1 webservice
    ' (parameters will change for production)
    ok = WSFEv1.Conectar("") ' testing
    
    ' Call dumy service to get server status (optional)
    WSFEv1.Dummy
    Debug.Print "appserver status", WSFEv1.AppServerStatus
    Debug.Print "dbserver status", WSFEv1.DbServerStatus
    Debug.Print "authserver status", WSFEv1.AuthServerStatus
       
    ' --------------------------------------------------
    ' MAIN Entry Point (routine to authorize an Invoice):
    ' --------------------------------------------------
        
StartCAERequest:
        
    ' IMPORTANT:
    ' Ignore COM errors, so normal execution sequence is not altered
    ' You must check errors manually reading WSFEv1.Excepcion 
    ' after each method call (not shown in this example!)
    ' If WSFEv1.Excepcion<>"", an unrecoverable error have occurred 
    ' (connection error, data type mismatch), you must check the source
    ' and restart the whole process.
    On Error Resume Next
    
    ' Set te invoice data to authorize (get CAE):
    tipo_cbte = 1      ' invoice type 1 : Invoice class A, 6: Invoice class B, etc.
    punto_vta = 4001#  ' point-of-sale number
    
    ' Get last invoice number authorized (like WSFE.RecuperaLastCMP)
    cbte_nro = WSFEv1.CompUltimoAutorizado(tipo_cbte, punto_vta)
    ' Set next invoice number:
    ' (this is illustrative, in a real system you must have invoice number and amounts in a database!)
    cbte_nro = cbte_nro + 1
    cbt_desde = cbte_nro
    cbt_hasta = cbte_nro
    
    fecha = Format(Date, "yyyymmdd") ' valid format is 20110525 (year, month, day)
    concepto = 1    ' concept: 1 products, 2 services, 3 products+services
    tipo_doc = 80   ' customer identification type 80: CUIT, 86: CUIL, 96: DNI, 99: Final Consumer
    nro_doc = "20267565393" ' customer identification number (CUIT)
        
    imp_total = "122.00"    ' total invoice amount
    imp_neto = "100.00"     ' net amount (for VAT)
    imp_iva = "21.00"       ' VAT amount
    imp_trib = "1.00"       ' NEW: other taxes total amount
    imp_op_ex = "0.00"      ' amount of operations VAT free
    imp_tot_conc = "0.00"   ' total amount not taxed
    
    fecha_cbte = fecha      ' invoice issue date
    fecha_venc_pago = fecha ' invoice due date
    
    ' Dates of service period (only if concept = 2)
    fecha_serv_desde = fecha: fecha_serv_hasta = fecha
    
    ' NEW: Currency code and quotation (exchange rate)
    moneda_id = "PES"
    moneda_ctz = "1.000"

    ' Create an invoice at the interface
    ' (internally, at this point, no webservice call is performed)
    ' This call is similar to WSFE.Aut (original webservice)
    ' Changes:
    '  * removed ID: sequence identification no longer used
    '  * added imp_trib: is the sum of all non VAT taxes
    '  * added currency
    
    ok = WSFEv1.CrearFactura(concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta, _
        cbt_desde, cbt_hasta, imp_total, imp_tot_conc, imp_neto, _
        imp_iva, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago, _
        fecha_serv_desde, fecha_serv_hasta, _
        moneda_id, moneda_ctz)
    
    ' NEW: Add asociated documents: Invoice numbers in case of credit/debit notes
    If tipo_cbte = 2 Or tipo_cbte = 7 Or tipo_cbte = 3 Or tipo_cbte = 8 Then
        tipo = 19
        pto_vta = 2
        nro = 1234
        ok = WSFEv1.AgregarCmpAsoc(tipo, pto_vta, nro)
    End If
        
    ' NEW: Add tax (must be repeated for each non VAT tax: federal, provincial or local)
    id = 99                                 ' tax code (see parameter table)
    Desc = "Impuesto Municipal Matanza'"    ' tax description
    base_imp = "100.00"                     ' tax net amount
    alic = "1.00"                           ' tax percentage
    importe = "1.00"                        ' tax amount
    ok = WSFEv1.AgregarTributo(id, Desc, base_imp, alic, importe)

    ' NEW: Add VAT tax subtotals (must be repeated for each VAT percentage)
    id = 5                  ' code for 21% VAT (see parameter table)
    base_im = "100.00"      ' net amount
    importe = "21.00"       ' VAT amount
    ok = WSFEv1.AgregarIva(id, base_imp, importe)
    
    ' NEW: CAE Request (perform webservice remote call)
    CAE = WSFEv1.CAESolicitar()
    
    Debug.Print "Resultado", WSFEv1.Resultado
    Debug.Print "CAE", WSFEv1.CAE
    Debug.Print "Numero de comprobante:", WSFEv1.CbteNro
        
    MsgBox "Result:" & WSFEv1.Resultado & _
           " CAE: " & CAE & " Due date: " & WSFEv1.Vencimiento & _
           " Obs: " & WSFEv1.obs & _ 
           " ErrMsg:" & WSFEv1.ErrMsg, vbInformation + vbOKOnly

    Debug.Print 

    ' Save XML messages for further reference:
    Debug.Print WSFEv1.XmlRequest
    Debug.Print WSFEv1.XmlResponse

    If WSFEv1.Excepcion<>"" Then
        MsgBox "Exception:" & WSFEv1.Excepcion
        ' Save Exception Traceback for degugging:
        Debug.Print WSFEv1.Traceback
        ' optionally, you can go to StartCAERequest
        ' to try to reprocess the invoice 
        '(if no data errors were found)
    Endif

    ' NEW: show AFIP events (scheduled maintance, etc.)
    For Each evento In WSFEv1.Eventos:
        MsgBox evento, vbInformation, "Evento"
    Next
    
    ' NEW WORKFLOW for error detection and retries:
    If WSFEv1.Resultado = "A" Then
InvoiceApproved:
        ' invoice approved!
        ' WSFEv1.CAE should have the electronic autorization number
        ' WSFEv1.Vencimiento should have the electronic autorization number due date
        ' (see WSFEv1.obs for AFIP messages regarding this invoice as it may be observed)
    ElseIf WSFEv1.Resultado = "R" Then
        ' invoice rejected!
        ' WSFEv1.CAE and WSFEv1.Vencimiento will be null
        ' Application shoud discard it or correct its errors
        ' (see WSFEv1.obs for a detailed error message regarding this invoice)
    Else
        ' Invoice status is undetermined (connection error, AFIP internal error, etc.)
        ' See WSFEv1.Errores or WSFEv1.ErrMsg for error message
        ' Must consult AFIP the status of the invoice:
        cae2 = WSFEv1.CompConsultar(tipo_cbte, punto_vta, cbte_nro)
        If WSFEv1.CAE Then
            ' invoice was authorized, check invoice data registered at AFIP:
            Debug.Print "Invoice Date:", WSFEv1.FechaCbte
            Debug.Print "CAE Due Date", WSFEv1.Vencimiento
            Debug.Print "Invoice Total amount:", WSFEv1.ImpTotal
            ' proceed as if WSFEv1.Resultado = "A"
            GoTo InvoiceApproved
            ' (goto is used just to illustrate the point)
        Else
            ' invoice was not authorized, retry this process or discard the invoice
            GoTo StartCAERequest
            ' (goto is used just to illustrate the point)
        End If
    End If
        
End Sub
```

## RECE1 Command Line tool ##

SIAP RECE is an interactive AFIP application to process electronic invoices using text files for legacy programming languages that doesn't support Webservice communication or encryption (but it doesn't uses webservices, so the communication process is cumbersome and the results take some time to arrive).

RECE1 is our tool that uses similar files but in a simplified way, no user interaction is required, with the advantage that communication is done instantaneously using webservices, so CAE number is returned immediately, no further process is needed, and can be done in background automatically.

### RECE1 Command line parameters ###
  * /ayuda: show help
  * /prueba: generate a test invoice and get CAE for it, saving input and ouput files with sample values. DO NOT USE IN PRODUCTION.
  * /ult: ask for invoice type and sale point, returns the last invoice number registered at AFIP
  * /dummy: queries AFIP server status (the three servers should return OK if they are working properly)
  * /debug: show extensive debug messages y and ask for confirmation prior sending the data to AFIP servers
  * /formato: show input/output file format
  * /get: recover previously authorized invoice, returns all informed data if available.
  * /xml: save XML request and response messages
  * /dbf: use DBF (Dbase III/FoxPro) tables instead of text files

### RECE1 Configuration File (rece.ini) ###

Before start using RECE1 tool, you must generate your private key and certificate files, and then edit the file RECE.INI in the interface folder (i.e. C:\WSFEv1):

Section [WSAA](WSAA.md):
  * CERT: path to the certificate file ()
  * PRIVATEKEY: path to the private key file
  * CUIT: CUIT of the company that generates the invoices
  * URL: location of the webservice (uncomment removing # to use in production, if not, it connects to testing servers "homologacion")

Section [WSFEv1](WSFEv1.md):
  * ENTRADA: path to the input text file
  * SALIDA: path to the ouput text file
  * URL: location of the webservice (uncomment removing # to use in production, if not, it connects to testing servers "homologacion")

Section [DBF](DBF.md): configure file name of DBF Tables (if /dbf is used)

Sample configuration file (minimal):
```
[WSAA]
CERT=homo.crt
PRIVATEKEY=homo.key
##URL=https://wsaa.afip.gov.ar/ws/services/LoginCms

[WSFEv1]
CUIT=30000000000
ENTRADA=entrada.txt
SALIDA=salida.txt
##URL=https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL
```

### RECE1 Usage ###
Sample usage (create a test invoice, show debug messages):
```
C:\WSFEv1>RECE1.EXE /debug /prueba
VERSION 1.29c HOMO True
CONFIG_FILE: rece.ini
wsaa_url https://wsaahomo.afip.gov.ar/ws/services/LoginCms
wsfev1_url None
cuit 20267565393
Autorizando usando entrada: entrada.txt
imp_total='122.0'
tipo_cbte='1'
moneda_ctz='1.0'
fecha_cbte='20110525'
imp_iva='21.0'
nro_doc='30628789661'
iva='[{'iva_id': u'5', 'base_imp': 100.0, 'importe': 21.0}]'
punto_vta='4002'
concepto='1'
cbtes_asoc='[]'
tipo_doc='80'
imp_op_ex='0.0'
tributos='[{'base_imp': 100.0, 'tributo_id': u'99', 'importe': 1.0, 'alic': 1.0, 'desc': u'Impuesto Municipal Matanza'}]'
imp_trib='1.0'
imp_neto='100.0'
cbt_desde='72'
moneda_id='PES'
cbt_hasta='72'
imp_tot_conc='0.0'
fecha_venc_pago=''
Facturar?S
NRO: 72 Resultado: A CAE: 61213036448700 Obs:  Err:  Reproceso: 
```

Normal usage (don't show debug messages nor make test invoice, but save XML files):
```
C:\WSFEv1>RECE1.EXE /xml
NRO: 72 Resultado: A CAE: 61213036448700 Obs:  Err:  Reproceso: S
```

Usage to query last invoice informed to AFIP and recover previously sent invoice data (Tipo de Comprobante: invoice type, Punto de Venta: point of sale, Ultimo numero: last invoice number):
```
C:\WSFEv1>RECE1.EXE /ult
Consultar ultimo numero:
Tipo de comprobante: 1
Punto de venta: 4002 
Ultimo numero:  72 

C:\WSFEv1>RECE1.EXE  /get
Recuperar comprobante:
Tipo de comprobante: 1
Punto de venta: 4002
Numero de comprobante: 72
FechaCbte =  20110525
CbteNro =  72
PuntoVenta =  4002
ImpTotal = 122.0
CAE =  61213036448700
Vencimiento =  20110604
EmisionTipo =  CAE
```

## RECE1 File Format ##

Input and output files have the same format, only returned fields are completed in the output file (cae, fch\_venc\_cae, resultado, errmsg, etc.)

Important: you must check current format with --formato parameter because you can have a another version with different field structure.

Records must be separated by line feed (LF) and/or carriage return (CR) depending the operating system convention.
Each record have a type in the first character (0: Invoice Header, 1: Other Taxes, 2: VAT Taxes, 3: Related Invoices):

### Invoice Header record ###
  * Field: tipo\_reg (record type)              Position:   1 Lenght:    1 Type: Numeric Decimals: Value: 0 (always)
  * Field: fecha\_cbte (invoice date)           Position:   2 Lenght:    8 Type: AlfaNumeric Decimals:
  * Field: tipo\_cbte (invoice type)             Position:  10 Lenght:    2 Type: Numeric Decimals:
  * Field: punto\_vta (point of sale)           Position:  12 Lenght:    4 Type: Numeric Decimals:
  * Field: cbt\_desde (invoice number from)           Position:  16 Lenght:    8 Type: Numeric Decimals:
  * Field: cbt\_hasta (invoice number to, same as invoice number from if authorizing only one invoice)           Position:  24 Lenght:    8 Type: Numeric Decimals:
  * Field: concepto (invoice concept, 1: products, 2: services, 3: product and services)             Position:  32 Lenght:    1 Type: Numeric Decimals:
  * Field: tipo\_doc (taxpayer identification type)             Position:  33 Lenght:    2 Type: Numeric Decimals:
  * Field: nro\_doc (taxpayer number)              Position:  35 Lenght:   11 Type: Numeric Decimals:
  * Field: imp\_total (total amount)            Position:  46 Lenght:   15 Type: Importe Decimals: 3
  * Field: no\_usar (not used, complete with blanks)             Position:  61 Lenght:   15 Type: Importe Decimals: 3
  * Field: imp\_tot\_conc (total amount not taxed)         Position:  76 Lenght:   15 Type: Importe Decimals: 3
  * Field: imp\_neto (net amount for VAT)            Position:  91 Lenght:   15 Type: Importe Decimals: 3
  * Field: imp\_iva (VAT amount)             Position: 106 Lenght:   15 Type: Importe Decimals: 3
  * Field: imp\_trib (other taxes amount)            Position: 121 Lenght:   15 Type: Importe Decimals: 3
  * Field: imp\_op\_ex (amount tax exempt)           Position: 136 Lenght:   15 Type: Importe Decimals: 3
  * Field: moneda\_id (currency code)           Position: 151 Lenght:    3 Type: AlfaNumeric Decimals:
  * Field: moneda\_ctz (currency quotation)           Position: 154 Lenght:   10 Type: Importe Decimals: 6
  * Field: fecha\_venc\_pago (payment due date)     Position: 164 Lenght:    8 Type: AlfaNumeric Decimals:
  * Field: cae                  Position: 172 Lenght:   14 Type: Numeric Decimals:
  * Field: fch\_venc\_cae (cae due date)         Position: 186 Lenght:    8 Type: AlfaNumeric Decimals:
  * Field: resultado (result, A: approved, R: rejected)           Position: 194 Lenght:    1 Type: AlfaNumeric Decimals:
  * Field: motivos\_obs (observation message)         Position: 195 Lenght: 1000 Type: AlfaNumeric Decimals:
  * Field: err\_code (error code)            Position: 1195 Lenght:    6 Type: AlfaNumeric Decimals:
  * Field: err\_msg (error message)            Position: 1201 Lenght: 1000 Type: AlfaNumeric Decimals:
  * Field: reproceso (reprocess previos sent invoice, blank: not needed, S: succed, N: fail, check data)           Position: 2201 Lenght:    1 Type: AlfaNumeric Decimals:
  * Field: emision\_tipo (electronic invoice type: CAE or CAEA)         Position: 2202 Lenght:    4 Type: AlfaNumeric Decimals:
  * Field: fecha\_serv\_desde (service date from)     Position: 2206 Lenght:    8 Type: AlfaNumeric Decimals:
  * Field: fecha\_serv\_hasta (service date to)    Position: 2214 Lenght:    8 Type: AlfaNumeric Decimals:

### Other taxes records (Tributos) ###
  * Field: Type\_reg             Position:   1 Lenght:    1 Type: Numeric Decimals: Value: 1 (always)
  * Field: tax\_id (tax code, see table)      Position:   2 Lenght:   16 Type: AlfaNumeric Decimals:
  * Field: desc (tax description)                 Position:  18 Lenght:  100 Type: AlfaNumeric Decimals:
  * Field: base\_imp (tax net amount)           Position: 118 Lenght:   15 Type: Importe Decimals: 3
  * Field: alic (tax aliquot/percentage)               Position: 133 Lenght:   15 Type: Importe Decimals: 3
  * Field: importe  (tax amount)             Position: 148 Lenght:   15 Type: Importe Decimals: 3

### VAT Tax records (IVA) ###
  * Field: tipo\_reg             Position:   1 Lenght:    1 Type: Numeric Decimals: Value: 2 (always)
  * Field: iva\_id (vat aliquot/percentage code, see table)                   Position:   2 Lenght:   16 Type: AlfaNumeric Decimals:
  * Field: base\_imp  (vat net amount)            Position:  18 Lenght:   15 Type: Importe Decimals: 3
  * Field: importe (vat amount)             Position:  33 Lenght:   15 Type: Importe Decimals: 3

### Related invoice records (Comprobante Asociado) ###
  * Field: tipo\_reg (record type)             Position:   1 Lenght:    1 Type: Numeric Decimals: Value: 3 (always)
  * Field: tipo (invoice type, see table) Position:   2 Lenght:    3 Type: Numeric Decimals:
  * Field: pto\_vta (sale point number)             Position:   5 Lenght:    4 Type: Numeric Decimals:
  * Field: nro (invoice number)                Position:   9 Lenght:    8 Type: Numeric Decimals:

## RECE1 WSFEv1 DBF Table Structure ##

The Optional DBF structure is similar to text file format exposed before, but each record type is stored in a separate table:

### Table Encabeza.dbf: Invoice header ###
  * tiporeg N(1,0)
  * fechacbte C(8)
  * tipocbte N(2,0)
  * puntovta N(4,0)
  * cbtdesde N(8,0)
  * cbthasta N(8,0)
  * concepto N(1,0)
  * tipodoc N(2,0)
  * nrodoc N(11,0)
  * imptotal N(15,3)
  * nousar N(15,3)
  * imptotconc N(15,3)
  * impneto N(15,3)
  * impiva N(15,3)
  * imptrib N(15,3)
  * impopex N(15,3)
  * monedaid C(3)
  * monedactz N(10,6)
  * fechavencp C(8)
  * cae N(14,0)
  * fchvenccae C(8)
  * resultado C(1)
  * motivosobs M
  * errcode C(6)
  * errmsg M
  * reproceso C(1)
  * emisiontip C(4)

### Table Tributo.dbf ###
  * tiporeg N(1,0)
  * tributo\_id C(16)
  * desc C(100)
  * baseimp N(15,3)
  * alic N(15,3)
  * importe N(15,3)

### Table Iva.dbf ###
  * tiporeg N(1,0)
  * iva\_id C(16)
  * baseimp N(15,3)
  * importe N(15,3)

### Table Comproba.dbf ###
  * tiporeg N(1,0)
  * tipo N(3,0)
  * ptovta N(4,0)
  * nro N(8,0)


## WSFEv1/RECE1 Parameter Tables ##

This webservice is parametrized with the following tables:

### Invoice Types (Tipos de Comprobante) ###

|Id (tipo\_cbte)|Desc (description)|FchDesde-FchHasta (applicable dates from-to)|
|:--------------|:-----------------|:-------------------------------------------|
|1 |Factura A (Invoice A)|(20100917-NULL)|
|2 |Nota de Débito A (Debit Note A)|(20100917-NULL)|
|3 |Nota de Crédito A (Credit Note A)|(20100917-NULL)|
|6 |Factura B (Invoice B)|(20100917-NULL)|
|7 |Nota de Débito B (Debit Note B)|(20100917-NULL)|
|8 |Nota de Crédito B (Credit Note B)|(20100917-NULL)|
|4 |Recibos A (Receipt A)|(20100917-NULL)|
|5 |Notas de Venta al contado A (Sale Note A -in cash-)|(20100917-NULL)|
|9 |Recibos B (Receipt B)|(20100917-NULL)|
|10|Notas de Venta al contado B (Sale Note B -in cash-)|(20100917-NULL)|
|63|Liquidacion A|(20100917-NULL)|
|64|Liquidacion B|(20100917-NULL)|
|34|Cbtes. A del Anexo I, Apartado A,inc.f),R.G.Nro. 1415|(20100917-NULL)|
|35|Cbtes. B del Anexo I,Apartado A,inc. f),R.G. Nro. 1415|(20100917-NULL)|
|39|Otros comprobantes A que cumplan con R.G.Nro. 1415|(20100917-NULL)|
|40|Otros comprobantes B que cumplan con R.G.Nro. 1415|(20100917-NULL)|
|60|Cta de Vta y Liquido prod. A|(20100917-NULL)|
|61|Cta de Vta y Liquido prod. B|(20100917-NULL)|
|11|Factura C (Invoice C)|(20110330-NULL)|
|12|Nota de Débito C (Debit Note C)|(20110330-NULL)|
|13|Nota de Crédito C (Credit Note C)|(20110330-NULL)|
|15|Recibo C (Receipt C)|(20110330-NULL)|

### Concept types (Tipos de Concepto) ###

|Id (concepto)|Desc (description)|FchDesde-FchHasta (applicable dates from-to)|
|:------------|:-----------------|:-------------------------------------------|
|1 |Producto (Products only)|(20100917-NULL)|
|2 |Servicios (Services only)|(20100917-NULL)|
|3 |Productos y Servicios (products and services)|(20100917-NULL)|

### Taxpayer document type (Tipos de Documento) ###

|Id (tipo\_doc)|Desc (description)|FchDesde-FchHasta (applicable dates from-to)|
|:-------------|:-----------------|:-------------------------------------------|
|80|CUIT|(20080725-NULL)|
|86|CUIL|(20080725-NULL)|
|87|CDI|(20080725-NULL)|
|89|LE|(20080725-NULL)|
|90|LC|(20080725-NULL)|
|91|CI Extranjera|(20080725-NULL)|
|92|en trámite|(20080725-NULL)|
|93|Acta Nacimiento|(20080725-NULL)|
|95|CI Bs. As. RNP|(20080725-NULL)|
|96|DNI|(20080725-NULL)|
|94|Pasaporte (Passport)|(20080725-NULL)|
|0 |CI Policía Federal|(20080725-NULL)|
|1 |CI Buenos Aires|(20080725-NULL)|
|2 |CI Catamarca|(20080725-NULL)|
|3 |CI Córdoba|(20080725-NULL)|
|4 |CI Corrientes|(20080728-NULL)|
|5 |CI Entre Ríos|(20080728-NULL)|
|6 |CI Jujuy|(20080728-NULL)|
|7 |CI Mendoza|(20080728-NULL)|
|8 |CI La Rioja|(20080728-NULL)|
|9 |CI Salta|(20080728-NULL)|
|10|CI San Juan|(20080728-NULL)|
|11|CI San Luis|(20080728-NULL)|
|12|CI Santa Fe|(20080728-NULL)|
|13|CI Santiago del Estero|(20080728-NULL)|
|14|CI Tucumán|(20080728-NULL)|
|16|CI Chaco|(20080728-NULL)|
|17|CI Chubut|(20080728-NULL)|
|18|CI Formosa|(20080728-NULL)|
|19|CI Misiones|(20080728-NULL)|
|20|CI Neuquén|(20080728-NULL)|
|21|CI La Pampa|(20080728-NULL)|
|22|CI Río Negro|(20080728-NULL)|
|23|CI Santa Cruz|(20080728-NULL)|
|24|CI Tierra del Fuego|(20080728-NULL)|
|99|Doc. -Otro- (Other - Final Consumer)|(20080728-NULL)|

### VAT TAX Aliquot/percentage (Alicuotas de IVA) ###

|Id (iva\_id)|Desc (description)|FchDesde-FchHasta (applicable dates from-to)|
|:-----------|:-----------------|:-------------------------------------------|
|3 |0%|(20090220-NULL)|
|4 |10.5%|(20090220-NULL)|
|5 |21%|(20090220-NULL)|
|6 |27%|(20090220-NULL)|

### Currencies (Monedas) ###

|Id (currency\_id)|Desc (description)|FchDesde-FchHasta (applicable dates from-to)|
|:----------------|:-----------------|:-------------------------------------------|
|PES|Pesos Argentinos (ARS)|(20090403-NULL)|
|DOL|Dólar Estadounidense (USD)|(20090403-NULL)|
|002|Dólar Libre EEUU (USD - free)|(20090416-NULL)|
|007|Florines Holandeses|(20090403-NULL)|
|010|Pesos Mejicanos (MXN)|(20090403-NULL)|
|011|Pesos Uruguayos (UYP)|(20090403-NULL)|
|014|Coronas Danesas (DKK)|(20090403-NULL)|
|015|Coronas Noruegas|(20090403-NULL)|
|016|Coronas Suecas|(20090403-NULL)|
|018|Dólar Canadiense (CAD)|(20090403-NULL)|
|019|Yens (JPY)|(20090403-NULL)|
|021|Libra Esterlina (GBP)|(20090403-NULL)|
|023|Bolívar Venezolano (VEB)|(20090403-NULL)|
|024|Corona Checa|(20090403-NULL)|
|025|Dinar Yugoslavo|(20090403-NULL)|
|026|Dólar Australiano (AUD)|(20090403-NULL)|
|027|Dracma Griego (GRD)|(20090403-NULL)|
|028|Florín (Antillas Holandesas)|(20090403-NULL)|
|029|Güaraní|(20090403-NULL)|
|031|Peso Boliviano (PYG)|(20090403-NULL)|
|032|Peso Colombiano (COP)|(20090403-NULL)|
|033|Peso Chileno (CLP)|(20090403-NULL)|
|034|Rand Sudafricano|(20090403-NULL)|
|036|Sucre Ecuatoriano|(20090403-NULL)|
|051|Dólar de Hong Kong (HKD)|(20090403-NULL)|
|052|Dólar de Singapur (SGD)|(20090403-NULL)|
|053|Dólar de Jamaica|(20090403-NULL)|
|054|Dólar de Taiwan (TWD)|(20090403-NULL)|
|055|Quetzal Guatemalteco|(20090403-NULL)|
|056|Forint (Hungría)|(20090403-NULL)|
|057|Baht (Tailandia)|(20090403-NULL)|
|059|Dinar Kuwaiti|(20090403-NULL)|
|012|Real (BRL)|(20090403-NULL)|
|030|Shekel (Israel)|(20090403-NULL)|
|035|Nuevo Sol Peruano|(20090403-NULL)|
|060|Euro (ECU)|(20090403-NULL)|
|040|Lei Rumano|(20090415-NULL)|
|042|Peso Dominicano|(20090415-NULL)|
|043|Balboas Panameñas|(20090415-NULL)|
|044|Córdoba Nicaragüense|(20090415-NULL)|
|045|Dirham Marroquí|(20090415-NULL)|
|046|Libra Egipcia|(20090415-NULL)|
|047|Riyal Saudita|(20090415-NULL)|
|061|Zloty Polaco|(20090415-NULL)|
|062|Rupia Hindú|(20090415-NULL)|
|063|Lempira Hondureña|(20090415-NULL)|
|064|Yuan (Rep. Pop. China) (RMB)|(20090415-NULL)|
|009|Franco Suizo (CHF)|(20091110-NULL)|
|041|Derechos Especiales de Giro|(20100125-NULL)|
|049|Gramos de Oro Fino|(20100125-NULL)|

### Optional Data (Tipos de datos opcionales) ###

|Id (opcional\_id)|Desc (description)|FchDesde-FchHasta (applicable dates from-to)|
|:----------------|:-----------------|:-------------------------------------------|
|2 |RG Empresas Promovidas - Indentificador de proyecto vinculado a Régimen de Promoción Industrial (promotional regime)|(20100917-NULL)|

### Other Taxes (Tipos de Tributo) ###

|Id (tributo\_id)|Desc (description)|FchDesde-FchHasta (applicable dates from-to)|
|:---------------|:-----------------|:-------------------------------------------|
|1 |Impuestos nacionales (National Taxes)|(20100917-NULL)|
|2 |Impuestos provinciales (Provincial/State Taxes)|(20100917-NULL)|
|3 |Impuestos municipales (Municipal/County Taxes)|(20100917-NULL)|
|4 |Impuestos Internos(Internal Taxes)|(20100917-NULL)|
|99|Otro (Other Taxes)|(20100917-NULL)|