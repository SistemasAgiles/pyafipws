#!/usr/bin/python
# -*- coding: latin-1 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"M�dulo de Intefase para archivos de texto (mercado interno versi�n 1)"

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2010-2014 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.33b"

import datetime
import os
import sys
import time
import traceback
from ConfigParser import SafeConfigParser

# revisar la instalaci�n de pyafip.ws:
import wsfev1
from php import SimpleXMLElement, SoapClient, SoapFault, date
from utils import leer, escribir, leer_dbf, guardar_dbf, N, A, I


HOMO = wsfev1.HOMO
DEBUG = False
XML = False
CONFIG_FILE = "rece.ini"

LICENCIA = """
rece1.py: Interfaz de texto para generar Facturas Electr�nica Mercado Interno V1
Copyright (C) 2010 Mariano Reingart reingart@gmail.com

Este progarma es software libre, se entrega ABSOLUTAMENTE SIN GARANTIA
y es bienvenido a redistribuirlo bajo la licencia GPLv3.

Para informaci�n adicional sobre garant�a, soporte t�cnico comercial
e incorporaci�n/distribuci�n en programas propietarios ver PyAfipWs:
http://www.sistemasagiles.com.ar/trac/wiki/PyAfipWs
"""

# definici�n del formato del archivo de intercambio:

ENCABEZADO = [
    ('tipo_reg', 1, N), # 0: encabezado
    ('fecha_cbte', 8, A),
    ('tipo_cbte', 2, N), ('punto_vta', 4, N),
    ('cbt_desde', 8, N), 
    ('cbt_hasta', 8, N), 
    ('concepto', 1, N), # 1:bienes, 2:servicios,... 
    ('tipo_doc', 2, N), # 80
    ('nro_doc', 11, N), # 50000000016    
    ('imp_total', 15, I, 2), 
    ('no_usar', 15, I, 2), 
    ('imp_tot_conc', 15, I, 2), 
    ('imp_neto', 15, I, 2), 
    ('imp_iva', 15, I, 2), 
    ('imp_trib', 15, I, 2), 
    ('imp_op_ex', 15, I, 2), 
    ('moneda_id', 3, A),
    ('moneda_ctz', 10, I, 6), #10,6
    ('fecha_venc_pago', 8, A),   # opcional solo conceptos 2 y 3
    ('cae', 14, A), ('fch_venc_cae', 8, A),
    ('resultado', 1, A), 
    ('motivos_obs', 1000, A),
    ('err_code', 6, A),
    ('err_msg', 1000, A),
    ('reproceso', 1, A),
    ('emision_tipo', 4, A),
    ('fecha_serv_desde', 8, A), # opcional solo conceptos 2 y 3
    ('fecha_serv_hasta', 8, A), # opcional solo conceptos 2 y 3
    ]
                   
#DETALLE = [
#    ('tipo_reg', 1, N), # 1: detalle item
#    ('codigo', 30, A),
#    ('qty', 12, I),
#    ('umed', 2, N),
#    ('precio', 12, I, 3),
#    ('imp_total', 14, I, 3),
#    ('ds', 4000, A),
#    ]

TRIBUTO = [
    ('tipo_reg', 1, N), # 1: tributo
    ('tributo_id', 16, N),
    ('desc', 100, A),
    ('base_imp', 15, I, 2), 
    ('alic', 15, I, 2), 
    ('importe', 15, I, 2), 
    ]

IVA = [
    ('tipo_reg', 1, N), # 2: tributo
    ('iva_id', 16, N),
    ('base_imp', 15, I, 2), 
    ('importe', 15, I, 2), 
    ]

CMP_ASOC = [
    ('tipo_reg', 1, N), # 3: comprobante asociado
    ('tipo', 3, N), ('pto_vta', 4, N),
    ('nro', 8, N), 
    ]

OPCIONAL = [
    ('tipo_reg', 1, N), # 6: datos opcionales
    ('opcional_id', 4, A),
    ('valor', 250, A), 
    ]


def autorizar(ws, entrada, salida, informar_caea=False):
    tributos = []
    ivas = []
    cbtasocs = []
    encabezado = []
    opcionales = []
    if '/dbf' in sys.argv:
        if DEBUG: print "Leyendo DBF..."

        formatos = [('Encabezado', ENCABEZADO, encabezado), 
                    ('Tributo', TRIBUTO, tributos), 
                    ('Iva', IVA, ivas), 
                    ('Comprobante Asociado', CMP_ASOC, cbtasocs),
                    ('Datos Adicionales', OPCIONAL, opcionales),
                    ]
        dic = leer_dbf(formatos, conf_dbf)
        encabezado = encabezado[0]
    elif '/json' in sys.argv:
        import json
        encabezado = json.load(entrada)[0]
        ivas = encabezado.get('ivas', [])
        tributos = encabezado.get('tributos', [])
        cbtasocs = encabezado.get('cbtasocs', [])
        opcionales = encabezado.get('opcionales', [])
    else:
        for linea in entrada:
            if str(linea[0])=='0':
                encabezado = leer(linea, ENCABEZADO)
            elif str(linea[0])=='1':
                tributo = leer(linea, TRIBUTO)
                tributos.append(tributo)
            elif str(linea[0])=='2':
                iva = leer(linea, IVA)
                ivas.append(iva)
            elif str(linea[0])=='3':
                cbtasoc = leer(linea, CMP_ASOC)
                cbtasocs.append(cbtasoc)
            elif str(linea[0])=='6':
                opcional = leer(linea, OPCIONAL)
                opcionales.append(opcional)
            else:
                print "Tipo de registro incorrecto:", linea[0]

    if informar_caea:
        if '/testing' in sys.argv:
            encabezado['cae'] = '21073372218437'
        encabezado['caea'] = encabezado['cae']

    if not encabezado:
        raise RuntimeError("No se pudieron leer los registros de la entrada")

    ws.CrearFactura(**encabezado)
    for tributo in tributos:
        ws.AgregarTributo(**tributo)
    for iva in ivas:
        ws.AgregarIva(**iva)
    for cbtasoc in cbtasocs:
        ws.AgregarCmpAsoc(**cbtasoc)
    for opcional in opcionales:
        ws.AgregarOpcional(**opcional)

    if DEBUG:
        print '\n'.join(["%s='%s'" % (k,str(v)) for k,v in ws.factura.items()])
    if not DEBUG or raw_input("Facturar?")=="S":
        if not informar_caea:
            cae = ws.CAESolicitar()
            dic = ws.factura
        else:
            cae = ws.CAEARegInformativo()
            dic = ws.factura
        dic.update(encabezado)         # preservar la estructura leida
        dic.update({
            'cae': cae and str(cae) or '',
            'fch_venc_cae': ws.Vencimiento and str(ws.Vencimiento) or '',
            'resultado': ws.Resultado,
            'motivos_obs': ws.Obs,
            'err_code': str(ws.ErrCode),
            'err_msg': ws.ErrMsg,
            'reproceso': ws.Reproceso,
            'emision_tipo': ws.EmisionTipo,
            })
        escribir_factura(dic, salida)
        print "NRO:", dic['cbt_desde'], "Resultado:", dic['resultado'], "%s:" % ws.EmisionTipo,dic['cae'],"Obs:",dic['motivos_obs'].encode("ascii", "ignore"), "Err:", dic['err_msg'].encode("ascii", "ignore"), "Reproceso:", dic['reproceso']

def escribir_factura(dic, archivo, agrega=False):
    if '/json' in sys.argv:
        import json
        json.dump([dic], archivo, sort_keys=True, indent=4)
    else:
        dic['tipo_reg'] = 0
        archivo.write(escribir(dic, ENCABEZADO))
        if 'tributos' in dic:
            for it in dic['tributos']:
                it['tipo_reg'] = 1
                archivo.write(escribir(it, TRIBUTO))
        if 'iva' in dic:
            for it in dic['iva']:
                it['tipo_reg'] = 2
                archivo.write(escribir(it, IVA))
        if 'cbtes_asoc' in dic:
            for it in dic['cbtes_asoc']:
                it['tipo_reg'] = 3
                archivo.write(escribir(it, CMP_ASOC))
        if 'opcionales' in dic:
            for it in dic['opcionales']:
                it['tipo_reg'] = 6
                archivo.write(escribir(it, OPCIONAL))

    if '/dbf' in sys.argv:
        formatos = [('Encabezado', ENCABEZADO, [dic]), 
                    ('Tributo', TRIBUTO, dic.get('tributos', [])), 
                    ('Iva', IVA, dic.get('iva', [])), 
                    ('Comprobante Asociado', CMP_ASOC, dic.get('cbtes_asoc', [])),
                    ('Datos Opcionales', OPCIONAL, dic.get("opcionales", [])),
                    ]
        guardar_dbf(formatos, agrega, conf_dbf)


def depurar_xml(client):
    fecha = time.strftime("%Y%m%d%H%M%S")
    f=open("request-%s.xml" % fecha,"w")
    f.write(client.xml_request)
    f.close()
    f=open("response-%s.xml" % fecha,"w")
    f.write(client.xml_response)
    f.close()

if __name__ == "__main__":
    if '/ayuda' in sys.argv:
        print LICENCIA
        print
        print "Opciones: "
        print " /ayuda: este mensaje"
        print " /dummy: consulta estado de servidores"
        print " /prueba: genera y autoriza una factura de prueba (no usar en producci�n!)"
        print " /ult: consulta �ltimo n�mero de comprobante"
        print " /debug: modo depuraci�n (detalla y confirma las operaciones)"
        print " /formato: muestra el formato de los archivos de entrada/salida"
        print " /get: recupera datos de un comprobante autorizado previamente (verificaci�n)"
        print " /xml: almacena los requerimientos y respuestas XML (depuraci�n)"
        print " /dbf: lee y almacena la informaci�n en tablas DBF"
        print
        print "Ver rece.ini para par�metros de configuraci�n (URL, certificados, etc.)"
        sys.exit(0)

    if '/debug'in sys.argv:
        DEBUG = True
        print "VERSION", __version__, "HOMO", HOMO

    if len(sys.argv)>1 and sys.argv[1][0] not in "-/":
        CONFIG_FILE = sys.argv.pop(1)
    if DEBUG: print "CONFIG_FILE:", CONFIG_FILE

    config = SafeConfigParser()
    config.read(CONFIG_FILE)
    #print CONFIG_FILE
    cert = config.get('WSAA','CERT')
    privatekey = config.get('WSAA','PRIVATEKEY')
    cuit = config.get('WSFEv1','CUIT')
    if '/entrada' in sys.argv:
        entrada = sys.argv[sys.argv.index("/entrada")+1]
    else:
        entrada = config.get('WSFEv1','ENTRADA')
    salida = config.get('WSFEv1','SALIDA')
    
    if config.has_option('WSAA','URL') and not HOMO:
        wsaa_url = config.get('WSAA','URL')
    else:
        wsaa_url = None
    if config.has_option('WSFEv1','URL') and not HOMO:
        wsfev1_url = config.get('WSFEv1','URL')
    else:
        wsfev1_url = None

    if config.has_option('WSFEv1','REPROCESAR'):
        wsfev1_reprocesar = config.get('WSFEv1','REPROCESAR') == 'S'
    else:
        wsfev1_reprocesar = None

    if config.has_option('WSFEv1', 'XML_DIR'):
        wsfev1_xml_dir = config.get('WSFEv1', 'XML_DIR')
    else:
        wsfev1_xml_dir = "."

    if config.has_section('DBF'):
        conf_dbf = dict(config.items('DBF'))
        if DEBUG: print "conf_dbf", conf_dbf
    else:
        conf_dbf = {}

    if config.has_section('PROXY') and not HOMO:
        proxy_dict = dict(("proxy_%s" % k,v) for k,v in config.items('PROXY'))
        proxy_dict['proxy_port'] = int(proxy_dict['proxy_port'])
    else:
        proxy_dict = {}
    CACERT = config.has_option('WSFEv1', 'CACERT') and config.get('WSFEv1', 'CACERT') or None
    WRAPPER = config.has_option('WSFEv1', 'WRAPPER') and config.get('WSFEv1', 'WRAPPER') or None

    if '/xml'in sys.argv:
        XML = True

    if DEBUG:
        print "wsaa_url %s\nwsfev1_url %s\ncuit %s" % (wsaa_url, wsfev1_url, cuit)
        if proxy_dict: print "proxy_dict=",proxy_dict

    if '/x' in sys.argv:
        escribir_factura({'err_msg': "Prueba",
                     }, open("x.txt","w"))

    try:
        ws = wsfev1.WSFEv1()
        ws.LanzarExcepciones = True
        ws.Conectar("", wsfev1_url, proxy=proxy_dict, cacert=CACERT, wrapper=WRAPPER)
        ws.Cuit = cuit
        if wsfev1_reprocesar is not None:
            ws.Reprocesar = wsfev1_reprocesar

        if '/dummy' in sys.argv:
            print "Consultando estado de servidores..."
            ws.Dummy()
            print "AppServerStatus", ws.AppServerStatus
            print "DbServerStatus", ws.DbServerStatus
            print "AuthServerStatus", ws.AuthServerStatus
            sys.exit(0)

        if '/formato' in sys.argv:
            print "Formato:"
            for msg, formato in [('Encabezado', ENCABEZADO), 
                                 ('Tributo', TRIBUTO), ('Iva', IVA), 
                                 ('Comprobante Asociado', CMP_ASOC),
                                 ('Opcionales', OPCIONAL)]:
                comienzo = 1
                print "== %s ==" % msg
                for fmt in formato:
                    clave, longitud, tipo = fmt[0:3]
                    dec = len(fmt)>3 and fmt[3] or (tipo=='I' and '2' or '')
                    print " * Campo: %-20s Posici�n: %3d Longitud: %4d Tipo: %s Decimales: %s" % (
                        clave, comienzo, longitud, tipo, dec)
                    comienzo += longitud
            sys.exit(0)

        # obteniendo el TA
        from wsaa import WSAA
        wsaa = WSAA()
        ta = wsaa.Autenticar("wsfe", cert, privatekey, wsaa_url, proxy=proxy_dict, cacert=CACERT, wrapper=WRAPPER)
        if not ta:
            sys.exit("Imposible autenticar con WSAA: %s" % wsaa.Excepcion)
        ws.SetTicketAcceso(ta)
                    
        if '/prueba' in sys.argv:
            # generar el archivo de prueba para la pr�xima factura
            tipo_cbte = 1
            punto_vta = 4002
            cbte_nro = ws.CompUltimoAutorizado(tipo_cbte, punto_vta)
            if not cbte_nro: cbte_nro=0
            cbte_nro=int(cbte_nro)
            fecha = datetime.datetime.now().strftime("%Y%m%d")
            concepto = 1
            tipo_doc = 80; nro_doc = "30628789661"
            cbt_desde = cbte_nro + 1; cbt_hasta = cbte_nro + 1
            imp_total = "122.00"; imp_tot_conc = "0.00"; imp_neto = "100.00"
            imp_iva = "21.00"; imp_trib = "1.00"; imp_op_ex = "0.00"
            fecha_cbte = fecha; fecha_venc_pago = None # fecha
            # Fechas del per�odo del servicio facturado (solo si concepto = 1?)
            fecha_serv_desde = ""; fecha_serv_hasta = ""
            moneda_id = 'PES'; moneda_ctz = '1.000'

            ws.CrearFactura(concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta,
                cbt_desde, cbt_hasta, imp_total, imp_tot_conc, imp_neto,
                imp_iva, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago, 
                fecha_serv_desde, fecha_serv_hasta, #--
                moneda_id, moneda_ctz)
            
            if tipo_cbte not in (1, 2, 6, 7):
                tipo = 1
                pto_vta = 2
                nro = 1234
                ws.AgregarCmpAsoc(tipo, pto_vta, nro)
            
            if '--proyectos' in sys.argv:
                ws.AgregarOpcional(2, "1234")  # identificador del proyecto
                     # datos opcionales para RG 3668 Impuesto al Valor Agregado - Art.12:
            if '--rg3668' in sys.argv:
                ws.AgregarOpcional(5, "02")             # IVA Excepciones
                ws.AgregarOpcional(61, "80")            # Firmante Doc Tipo
                ws.AgregarOpcional(62, "20267565393")   # Firmante Doc Nro
                ws.AgregarOpcional(7, "01")             # Car�cter del Firmante
                
            tributo_id = 99
            desc = 'Impuesto Municipal Matanza'
            base_imp = 100
            alic = 1
            importe = 1
            ws.AgregarTributo(tributo_id, desc, base_imp, alic, importe)

            iva_id = 5 # 21%
            base_imp = 100
            importe = 21
            ws.AgregarIva(iva_id, base_imp, importe) 
                        
            f_entrada = open(entrada,"w")
                
            if DEBUG:
                print ws.factura

            dic = ws.factura
            escribir_factura(dic, f_entrada, agrega=True)
            f_entrada.close()
      
        if '/ult' in sys.argv:
            print "Consultar ultimo numero:"
            i = sys.argv.index("/ult")
            if i+2<len(sys.argv):
               tipo_cbte = int(sys.argv[i+1])
               punto_vta = int(sys.argv[i+2])
            else:
               tipo_cbte = int(raw_input("Tipo de comprobante: "))
               punto_vta = int(raw_input("Punto de venta: "))
            ult_cbte = ws.CompUltimoAutorizado(tipo_cbte, punto_vta)
            print "Ultimo numero: ", ult_cbte
            print ws.ErrMsg
            depurar_xml(ws.client)
            escribir_factura({'tipo_cbte': tipo_cbte, 
                              'punto_vta': punto_vta, 
                              'cbt_desde': ult_cbte, 
                              'fecha_cbte': ws.FechaCbte, 
                              'err_msg': ws.ErrMsg,
                              }, open(salida,"w"))
            sys.exit(0)

        if '/get' in sys.argv:
            print "Recuperar comprobante:"
            i = sys.argv.index("/get")
            if i+3<len(sys.argv):
               tipo_cbte = int(sys.argv[i+1])
               punto_vta = int(sys.argv[i+2])
               cbte_nro = int(sys.argv[i+3])
            else:
               tipo_cbte = int(raw_input("Tipo de comprobante: "))
               punto_vta = int(raw_input("Punto de venta: "))
               cbte_nro = int(raw_input("Numero de comprobante: "))
            ws.CompConsultar(tipo_cbte, punto_vta, cbte_nro)

            ws.AnalizarXml("XmlResponse")
            print "FechaCbte = ", ws.FechaCbte
            print "CbteNro = ", ws.CbteNro
            print "PuntoVenta = ", ws.PuntoVenta
            print "TipoDoc = ", ws.ObtenerTagXml('DocTipo')
            print "NroDoc = ", ws.ObtenerTagXml('DocNro')
            print "ImpTotal =", ws.ImpTotal
            print "CAE = ", ws.CAE
            print "Vencimiento = ", ws.Vencimiento
            print "EmisionTipo = ", ws.EmisionTipo
            print ws.ErrMsg 

            depurar_xml(ws.client)
            escribir_factura({'tipo_cbte': tipo_cbte, 
                              'punto_vta': ws.PuntoVenta, 
                              'cbt_desde': ws.CbteNro, 
                              'fecha_cbte': ws.FechaCbte, 
                              'imp_total': ws.ImpTotal, 
                              'cae': str(ws.CAE), 
                              'fch_venc_cae': ws.Vencimiento,  
                              'emision_tipo': ws.EmisionTipo, 
                              'err_msg': ws.ErrMsg,
                            }, open(salida,"w"))

            sys.exit(0)

        if '/solicitarcaea' in sys.argv:
            i = sys.argv.index("/solicitarcaea")
            if i+2<len(sys.argv):
                periodo = sys.argv[sys.argv.index("/solicitarcaea")+1]
                orden = sys.argv[sys.argv.index("/solicitarcaea")+2]
            else:
                periodo = raw_input("Periodo: ")
                orden = raw_input("Orden: ")
                
            if DEBUG: 
                print "Solicitando CAEA para periodo %s orden %s" % (periodo, orden)
            
            caea = ws.CAEASolicitar(periodo, orden)
            print "CAEA:", caea

            if ws.Errores:
                print "Errores:"
                for error in ws.Errores:
                    print error

            depurar_xml(ws.client)

            if not caea:
                if DEBUG: 
                    print "Consultando CAEA para periodo %s orden %s" % (periodo, orden)
                caea = ws.CAEAConsultar(periodo, orden)
                print "CAEA:", caea
                
            if DEBUG:
                print "Periodo:", ws.Periodo 
                print "Orden:", ws.Orden 
                print "FchVigDesde:", ws.FchVigDesde 
                print "FchVigHasta:", ws.FchVigHasta 
                print "FchTopeInf:", ws.FchTopeInf 
                print "FchProceso:", ws.FchProceso

            escribir_factura({'cae': str(caea), 
                              'emision_tipo': "CAEA", 
                             }, open(salida,"w"))
                              
            sys.exit(0)

        if '/consultarcaea' in sys.argv:
            i = sys.argv.index("/consultarcaea")
            if i+2<len(sys.argv):
                periodo = sys.argv[sys.argv.index("/consultarcaea")+1]
                orden = sys.argv[sys.argv.index("/consultarcaea")+2]
            else:
                periodo = raw_input("Periodo: ")
                orden = raw_input("Orden: ")

            if DEBUG: 
                print "Consultando CAEA para periodo %s orden %s" % (periodo, orden)
            
            caea = ws.CAEAConsultar(periodo, orden)
            print "CAEA:", caea

            if ws.Errores:
                print "Errores:"
                for error in ws.Errores:
                    print error
                
            if DEBUG:
                print "Periodo:", ws.Periodo 
                print "Orden:", ws.Orden 
                print "FchVigDesde:", ws.FchVigDesde 
                print "FchVigHasta:", ws.FchVigHasta 
                print "FchTopeInf:", ws.FchTopeInf
                print "FchProceso:", ws.FchProceso
            sys.exit(0)

        if '/ptosventa' in sys.argv:

            print "=== Puntos de Venta ==="
            print u'\n'.join(ws.ParamGetPtosVenta())
            sys.exit(0)


        ws.LanzarExcepciones = False
        f_entrada = f_salida = None
        try:
            f_entrada = open(entrada,"r")
            f_salida = open(salida,"w")
            try:
                if DEBUG: print "Autorizando usando entrada:", entrada
                autorizar(ws, f_entrada, f_salida, '/informarcaea' in sys.argv)
            except SoapFault:
                XML = True
                raise
        finally:
            if f_entrada is not None: f_entrada.close()
            if f_salida is not None: f_salida.close()
            if XML:
                depurar_xml(ws.client)
        sys.exit(0)
    
    except SoapFault, e:
        print "SoapFault:", e.faultcode, e.faultstring.encode("ascii","ignore")
        sys.exit(3)
    except Exception, e:
        e_str = unicode(e).encode("ascii","ignore")
        if not e_str:
            e_str = repr(e)
        print "Excepcion:", e_str
        escribir_factura({'err_msg': e_str,
                         }, open(salida,"w"))
        ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
        open("traceback.txt", "wb").write('\n'.join(ex))

        if DEBUG:
            raise
        sys.exit(5)
