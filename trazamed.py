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

"""M�dulo para Trazabilidad de Medicamentos ANMAT - PAMI - INSSJP Disp. 3683/11
seg�n Especificaci�n T�cnica para Pruebas de Servicios v2 (2013)"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2011 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.10a"

import os
import socket
import sys
import datetime, time
import traceback
import pysimplesoap.client
from pysimplesoap.client import SoapClient, SoapFault, parse_proxy, \
                                set_http_wrapper
from pysimplesoap.simplexml import SimpleXMLElement
from cStringIO import StringIO

HOMO = False
TYPELIB = False

WSDL = "https://servicios.pami.org.ar/trazamed.WebService?wsdl"
LOCATION = "https://servicios.pami.org.ar/trazamed.WebService"
#WSDL = "https://trazabilidad.pami.org.ar:9050/trazamed.WebService?wsdl"
         
def inicializar_y_capturar_excepciones(func):
    "Decorador para inicializar y capturar errores"
    def capturar_errores_wrapper(self, *args, **kwargs):
        try:
            # inicializo (limpio variables)
            self.Resultado = self.CodigoTransaccion = ""
            self.Errores = []
            self.CantPaginas = self.HayError = None
            self.TransaccionPlainWS = []
            self.Traceback = self.Excepcion = ""
            
            if self.client is None:
                raise RuntimeError("Debe llamar a Conectar")

            # llamo a la funci�n (sin reintentos)
            return func(self, *args, **kwargs)

        except Exception, e:
            ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
            self.Traceback = ''.join(ex)
            try:
                self.Excepcion = traceback.format_exception_only( sys.exc_type, sys.exc_value)[0]
            except:
                self.Excepcion = u"<no disponible>"
            return False
        finally:
            # guardo datos de depuraci�n
            if self.client:
                self.XmlRequest = self.client.xml_request
                self.XmlResponse = self.client.xml_response
    return capturar_errores_wrapper


class TrazaMed:
    "Interfaz para el WebService de Trazabilidad de Medicamentos ANMAT - PAMI - INSSJP"
    _public_methods_ = ['SendMedicamentos',
                        'SendCancelacTransacc',
                        'SendMedicamentosDHSerie',
                        'SendMedicamentosFraccion',
                        'SendConfirmaTransacc', 'SendAlertaTransacc',
                        'GetTransaccionesNoConfirmadas',
                        'Conectar', 'LeerError', 'LeerTransaccion',
                        'SetUsername', 
                        'SetParametro', 'GetParametro',
                        'GetCodigoTransaccion', 'GetResultado', 'LoadTestXML']
                        
    _public_attrs_ = [
        'Username', 'Password', 
        'CodigoTransaccion', 'Errores', 'Resultado',
        'XmlRequest', 'XmlResponse', 
        'Version', 'InstallDir', 
        'Traceback', 'Excepcion',
        'CantPaginas', 'HayError', 'TransaccionPlainWS',
        ]

    _reg_progid_ = "TrazaMed"
    _reg_clsid_ = "{8472867A-AE6F-487F-8554-C2C896CFFC3E}"

    if TYPELIB:
        _typelib_guid_ = '{F992EB7E-AFBD-41BB-B717-5693D3A2BADB}'
        _typelib_version_ = 1, 4
        _com_interfaces_ = ['ITrazaMed']

    Version = "%s %s %s" % (__version__, HOMO and 'Homologaci�n' or '', 
                            pysimplesoap.client.__version__)

    def __init__(self):
        self.Username = self.Password = None
        self.CodigoTransaccion = self.Errores = self.Resultado = None
        self.XmlRequest = ''
        self.XmlResponse = ''
        self.Resultado = ''
        self.client = None
        self.Traceback = self.Excepcion = ""
        self.Log = None
        self.InstallDir = INSTALL_DIR
        self.params = {}

    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        self.Errores = ["%s: %s" % (it['_c_error'], it['_d_error'])
                        for it in ret.get('errores', [])]
        self.Resultado = ret.get('resultado')

    def Conectar(self, cache=None, wsdl=None, proxy="", wrapper=None, cacert=None):
        # cliente soap del web service
        try:
            if wrapper:
                Http = set_http_wrapper(wrapper)
                self.Version = TrazaMed.Version + " " + Http._wrapper_version
            proxy_dict = parse_proxy(proxy)
            if HOMO or not wsdl:
                wsdl = WSDL
                location = LOCATION
            if not wsdl.endswith("?wsdl") and wsdl.startswith("http"):
                location = wsdl
                wsdl += "?wsdl"
            elif wsdl.endswith("?wsdl"):
                location = wsdl[:-5]
            if not cache or HOMO:
                # use 'cache' from installation base directory 
                cache = os.path.join(self.InstallDir, 'cache')
            if "--trace" in sys.argv:
                print "Conectando a wsdl=%s cache=%s proxy=%s" % (wsdl, cache, proxy_dict)
            self.client = SoapClient(
                wsdl = wsdl,        
                cache = cache,
                proxy = proxy_dict,
                ns="tzmed",
                cacert=cacert,
                soap_ns="soapenv",
                soap_server="jetty",
                trace = "--trace" in sys.argv)
                
            # corrijo ubicaci�n del servidor (localhost:9050 en el WSDL)
            if 'IWebServiceService' in self.client.services:
                ws = self.client.services['IWebServiceService']  # version 1
            else:
                ws = self.client.services['IWebService']         # version 2
            ws['ports']['IWebServicePort']['location'] = location
            
            # Establecer credenciales de seguridad:
            self.client['wsse:Security'] = {
                'wsse:UsernameToken': {
                    'wsse:Username': self.Username,
                    'wsse:Password': self.Password,
                    }
                }
            return True
        except:
            ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
            self.Traceback = ''.join(ex)
            try:
                self.Excepcion = traceback.format_exception_only( sys.exc_type, sys.exc_value)[0]
            except:
                self.Excepcion = u"<no disponible>"
            return False

    def SetParametro(self, clave, valor):
        "Establece un par�metro general (usarse en llamadas posteriores)"
        # �til para par�metros de entrada (por ej. VFP9 no soporta m�s de 27)
        self.params[clave] = valor
        return True

    def GetParametro(self, clave):
        "Devuelve un par�metro general (establecido por llamadas anteriores)"
        # �til para par�metros de salida (por ej. campos de TransaccionPlainWS)
        return self.params.get(clave)
        
    @inicializar_y_capturar_excepciones
    def SendMedicamentos(self, usuario, password, 
                         f_evento, h_evento, gln_origen, gln_destino, 
                         n_remito, n_factura, vencimiento, gtin, lote,
                         numero_serial, id_obra_social, id_evento,
                         cuit_origen='', cuit_destino='', apellido='', nombres='',
                         tipo_docmento='', n_documento='', sexo='',
                         direccion='', numero='', piso='', depto='', localidad='', provincia='',
                         n_postal='', fecha_nacimiento='', telefono='',
                         nro_asociado=None,
                         ):
        "Realiza el registro de una transacci�n de medicamentos. "
        # creo los par�metros para esta llamada
        params = {  'f_evento': f_evento, 
                    'h_evento': h_evento, 
                    'gln_origen': gln_origen, 
                    'gln_destino': gln_destino, 
                    'n_remito': n_remito, 
                    'n_factura': n_factura, 
                    'vencimiento': vencimiento, 
                    'gtin': gtin, 
                    'lote': lote, 
                    'numero_serial': numero_serial, 
                    'id_obra_social': id_obra_social, 
                    'id_evento': id_evento, 
                    'cuit_origen': cuit_origen, 
                    'cuit_destino': cuit_destino, 
                    'apellido': apellido, 
                    'nombres': nombres, 
                    'tipo_docmento': tipo_docmento, 
                    'n_documento': n_documento, 
                    'sexo': sexo, 
                    'direccion': direccion, 
                    'numero': numero, 
                    'piso': piso, 
                    'depto': depto, 
                    'localidad': localidad, 
                    'provincia': provincia, 
                    'n_postal': n_postal,
                    'fecha_nacimiento': fecha_nacimiento, 
                    'telefono': telefono,
                    'nro_asociado': nro_asociado,
                    }
        # actualizo con par�metros generales:
        params.update(self.params)
        res = self.client.sendMedicamentos(
            arg0=params,
            arg1=usuario, 
            arg2=password,
        )

        ret = res['return']
        
        self.CodigoTransaccion = ret['codigoTransaccion']
        self.__analizar_errores(ret)

        return True

    @inicializar_y_capturar_excepciones
    def SendMedicamentosFraccion(self, usuario, password, 
                         f_evento, h_evento, gln_origen, gln_destino, 
                         n_remito, n_factura, vencimiento, gtin, lote,
                         numero_serial, id_obra_social, id_evento,
                         cuit_origen='', cuit_destino='', apellido='', nombres='',
                         tipo_docmento='', n_documento='', sexo='',
                         direccion='', numero='', piso='', depto='', localidad='', provincia='',
                         n_postal='', fecha_nacimiento='', telefono='',
                         nro_asociado=None, cantidad=None,
                         ):
        "Realiza el registro de una transacci�n de medicamentos fraccionados"
        # creo los par�metros para esta llamada
        params = {  'f_evento': f_evento, 
                    'h_evento': h_evento, 
                    'gln_origen': gln_origen, 
                    'gln_destino': gln_destino, 
                    'n_remito': n_remito, 
                    'n_factura': n_factura, 
                    'vencimiento': vencimiento, 
                    'gtin': gtin, 
                    'lote': lote, 
                    'numero_serial': numero_serial, 
                    'id_obra_social': id_obra_social, 
                    'id_evento': id_evento, 
                    'cuit_origen': cuit_origen, 
                    'cuit_destino': cuit_destino, 
                    'apellido': apellido, 
                    'nombres': nombres, 
                    'tipo_docmento': tipo_docmento, 
                    'n_documento': n_documento, 
                    'sexo': sexo, 
                    'direccion': direccion, 
                    'numero': numero, 
                    'piso': piso, 
                    'depto': depto, 
                    'localidad': localidad, 
                    'provincia': provincia, 
                    'n_postal': n_postal,
                    'fecha_nacimiento': fecha_nacimiento, 
                    'telefono': telefono,
                    'nro_asociado': nro_asociado,
                    'cantidad': cantidad,
                    }
        # actualizo con par�metros generales:
        params.update(self.params)
        res = self.client.sendMedicamentosFraccion(
            arg0=params,                    
            arg1=usuario, 
            arg2=password,
        )

        ret = res['return']
        
        self.CodigoTransaccion = ret['codigoTransaccion']
        self.__analizar_errores(ret)

        return True
        
    @inicializar_y_capturar_excepciones
    def SendMedicamentosDHSerie(self, usuario, password, 
                         f_evento, h_evento, gln_origen, gln_destino, 
                         n_remito, n_factura, vencimiento, gtin, lote,
                         desde_numero_serial, hasta_numero_serial,
                         id_obra_social, id_evento,
                         cuit_origen='', cuit_destino='', apellido='', nombres='',
                         tipo_docmento='', n_documento='', sexo='',
                         direccion='', numero='', piso='', depto='', localidad='', provincia='',
                         n_postal='', fecha_nacimiento='', telefono='',
                         nro_asociado=None,
                         ):
        "Env�a un lote de medicamentos informando el desde-hasta n�mero de serie"
        # creo los par�metros para esta llamada
        params = {  'f_evento': f_evento, 
                    'h_evento': h_evento, 
                    'gln_origen': gln_origen, 
                    'gln_destino': gln_destino, 
                    'n_remito': n_remito, 
                    'n_factura': n_factura, 
                    'vencimiento': vencimiento, 
                    'gtin': gtin, 
                    'lote': lote, 
                    'desde_numero_serial': desde_numero_serial, 
                    'hasta_numero_serial': hasta_numero_serial, 
                    'id_obra_social': id_obra_social, 
                    'id_evento': id_evento, 
                    'cuit_origen': cuit_origen, 
                    'cuit_destino': cuit_destino, 
                    'apellido': apellido, 
                    'nombres': nombres, 
                    'tipo_docmento': tipo_docmento, 
                    'n_documento': n_documento, 
                    'sexo': sexo, 
                    'direccion': direccion, 
                    'numero': numero, 
                    'piso': piso, 
                    'depto': depto, 
                    'localidad': localidad, 
                    'provincia': provincia, 
                    'n_postal': n_postal,
                    'fecha_nacimiento': fecha_nacimiento, 
                    'telefono': telefono,
                    'nro_asociado': nro_asociado,
                    }
        # actualizo con par�metros generales:
        params.update(self.params)
        res = self.client.sendMedicamentosDHSerie(
            arg0=params,
            arg1=usuario, 
            arg2=password,
        )

        ret = res['return']
        
        self.CodigoTransaccion = ret['codigoTransaccion']
        self.__analizar_errores(ret)

        return True

    @inicializar_y_capturar_excepciones
    def SendCancelacTransacc(self, usuario, password, codigo_transaccion):
        " Realiza la cancelaci�n de una transacci�n"
        res = self.client.sendCancelacTransacc(
            arg0=codigo_transaccion, 
            arg1=usuario, 
            arg2=password,
        )

        ret = res['return']
        
        self.CodigoTransaccion = ret['codigoTransaccion']
        self.__analizar_errores(ret)

        return True

    @inicializar_y_capturar_excepciones
    def SendConfirmaTransacc(self, usuario, password, p_ids_transac, f_operacion):
        "Confirma la recepci�n de un medicamento"
        res = self.client.sendConfirmaTransacc(
            arg0=usuario, 
            arg1=password,
            arg2={'p_ids_transac': p_ids_transac, 'f_operacion': f_operacion}, 
        )
        ret = res['return']
        self.CodigoTransaccion = ret.get('id_transac_asociada')
        self.__analizar_errores(ret)
        return True

    @inicializar_y_capturar_excepciones
    def SendAlertaTransacc(self, usuario, password, p_ids_transac_ws):
        "Alerta un medicamento, acci�n contraria a �confirmar la transacci�n�."
        res = self.client.sendAlertaTransacc(
            arg0=usuario, 
            arg1=password,
            arg2=p_ids_transac_ws, 
        )
        ret = res['return']
        self.CodigoTransaccion = ret.get('id_transac_asociada')
        self.__analizar_errores(ret)
        return True

    @inicializar_y_capturar_excepciones
    def GetTransaccionesNoConfirmadas(self, usuario, password, 
                p_id_transaccion_global=None, id_agente_informador=None, 
                id_agente_origen=None, id_agente_destino=None, 
                id_medicamento=None, id_evento=None, 
                fecha_desde_op=None, fecha_hasta_op=None, 
                fecha_desde_t=None, fecha_hasta_t=None, 
                fecha_desde_v=None, fecha_hasta_v=None, 
                n_remito=None, n_factura=None,
                estado=None,
                ):
        "Trae un listado de las transacciones que no est�n confirmadas"

        # preparo los parametros de entrada opcionales:
        kwargs = {}
        if p_id_transaccion_global is not None:
            kwargs['arg2'] = p_id_transaccion_global
        if id_agente_informador is not None:
            kwargs['arg3'] = id_agente_informador
        if id_agente_origen is not None:
            kwargs['arg4'] = id_agente_origen
        if id_agente_destino is not None: 
            kwargs['arg5'] = id_agente_destino
        if id_medicamento is not None: 
            kwargs['arg6'] = id_medicamento
        if id_evento is not None: 
            kwargs['arg7'] = id_evento
        if fecha_desde_op is not None: 
            kwargs['arg8'] = fecha_desde_op
        if fecha_hasta_op is not None: 
            kwargs['arg9'] = fecha_hasta_op
        if fecha_desde_t is not None: 
            kwargs['arg10'] = fecha_desde_t
        if fecha_hasta_t is not None: 
            kwargs['arg11'] = fecha_hasta_t
        if fecha_desde_v is not None: 
            kwargs['arg12'] = fecha_desde_v
        if fecha_hasta_v is not None: 
            kwargs['arg13'] = fecha_hasta_v
        if n_remito is not None: 
            kwargs['arg14'] = n_remito
        if n_factura is not None: 
            kwargs['arg15'] = n_factura
        if estado is not None: 
            kwargs['arg16'] = estado

        # llamo al webservice
        res = self.client.getTransaccionesNoConfirmadas(
            arg0=usuario, 
            arg1=password,
            **kwargs
        )
        ret = res['return']
        if ret:
            self.__analizar_errores(ret)
            self.CantPaginas = ret.get('cantPaginas')
            self.HayError = ret.get('hay_error')
            self.TransaccionPlainWS = [it for it in ret.get('list', [])]
        return True

    def  LeerTransaccion(self):
        "Recorro TransaccionPlainWS devuelto por GetTransaccionesNoConfirmadas"
         # usar GetParametro para consultar el valor retornado por el webservice
        
        if self.TransaccionPlainWS:
            # extraigo el primer item
            self.params = self.TransaccionPlainWS.pop(0)
            return True
        else:
            # limpio los par�metros
            self.params = {}
            return False

    def LeerError(self):
        "Recorro los errores devueltos y devuelvo el primero si existe"
        
        if self.Errores:
            # extraigo el primer item
            er = self.Errores.pop(0)
            return er
        else:
            return ""

    def SetUsername(self, username):
        "Establezco el nombre de usuario"        
        self.Username = username

    def SetPassword(self, password):
        "Establezco la contrase�a"        
        self.Password = password

    def GetCodigoTransaccion(self):
        "Devuelvo el c�digo de transacci�n"        
        return self.CodigoTransaccion

    def GetResultado(self):
        "Devuelvo el resultado"        
        return self.Resultado

    def LoadTestXML(self, xml_file):
        "Cargar una respuesta predeterminada de pruebas (emulaci�n del ws)"
        # cargo el ejemplo de AFIP (emulando respuesta del webservice)
        from pysimplesoap.transport import DummyTransport as DummyHTTP 
        xml = open(os.path.join(INSTALL_DIR, xml_file)).read()
        self.client.http = DummyHTTP(xml)


def main():
    "Funci�n principal de pruebas (obtener CAE)"
    import os, time, sys
    global WSDL, LOCATION

    DEBUG = '--debug' in sys.argv

    ws = TrazaMed()
    
    ws.Username = 'testwservice'
    ws.Password = 'testwservicepsw'
    
    if '--prod' in sys.argv and not HOMO:
        WSDL = "https://trazabilidad.pami.org.ar:9050/trazamed.WebService"
        print "Usando WSDL:", WSDL
        sys.argv.pop(0)
    
    ws.Conectar("", WSDL)
    
    if ws.Excepcion:
        print ws.Excepcion
        print ws.Traceback
        sys.exit(-1)
    
    #print ws.client.services
    #op = ws.client.get_operation("sendMedicamentos")
    #import pdb;pdb.set_trace()
    if '--test' in sys.argv:
        ws.SetParametro('nro_asociado', "9999999999999")
        ws.SendMedicamentos(
            usuario='pruebasws', password='pruebasws',
            f_evento=datetime.datetime.now().strftime("%d/%m/%Y"),
            h_evento=datetime.datetime.now().strftime("%H:%M"), 
            gln_origen="9999999999918", gln_destino="glnws", 
            n_remito="1234", n_factura="1234", 
            vencimiento=(datetime.datetime.now()+datetime.timedelta(30)).strftime("%d/%m/%Y"), 
            gtin="GTIN1", lote=datetime.datetime.now().strftime("%Y"),
            numero_serial=int(time.time()), 
            id_obra_social=None, id_evento=134,
            cuit_origen="20267565393", cuit_destino="20267565393", 
            apellido="Reingart", nombres="Mariano",
            tipo_docmento="96", n_documento="26756539", sexo="M",
            direccion="Saraza", numero="1234", piso="", depto="", 
            localidad="Hurlingham", provincia="Buenos Aires",
            n_postal="1688", fecha_nacimiento="01/01/2000", 
            telefono="5555-5555",
            )
        print "Resultado", ws.Resultado
        print "CodigoTransaccion", ws.CodigoTransaccion
        print "Excepciones", ws.Excepcion
        print "Erroes", ws.Errores
    if '--testfraccion' in sys.argv:
        ws.SetParametro('nro_asociado', "9999999999999")
        ws.SetParametro('cantidad', 5)
        ws.SendMedicamentosFraccion(
            usuario='pruebasws', password='pruebasws',
            f_evento=datetime.datetime.now().strftime("%d/%m/%Y"),
            h_evento=datetime.datetime.now().strftime("%H:%M"), 
            gln_origen="9999999999918", gln_destino="glnws", 
            n_remito="1234", n_factura="1234", 
            vencimiento=(datetime.datetime.now()+datetime.timedelta(30)).strftime("%d/%m/%Y"), 
            gtin="GTIN1", lote=datetime.datetime.now().strftime("%Y"),
            numero_serial=int(time.time()), 
            id_obra_social=None, id_evento=134,
            cuit_origen="20267565393", cuit_destino="20267565393", 
            apellido="Reingart", nombres="Mariano",
            tipo_docmento="96", n_documento="26756539", sexo="M",
            direccion="Saraza", numero="1234", piso="", depto="", 
            localidad="Hurlingham", provincia="Buenos Aires",
            n_postal="1688", fecha_nacimiento="01/01/2000", 
            telefono="5555-5555",)
        print "Resultado", ws.Resultado
        print "CodigoTransaccion", ws.CodigoTransaccion
        print "Erroes", ws.Errores
    elif '--testdh' in sys.argv:
        print "Informando medicamentos..."
        ws.SetParametro('nro_asociado', "1234")
        ws.SendMedicamentosDHSerie(
            usuario='pruebasws', password='pruebasws',
            f_evento=datetime.datetime.now().strftime("%d/%m/%Y"),
            h_evento=datetime.datetime.now().strftime("%H:%M"), 
            gln_origen="9999999999918", gln_destino="glnws", 
            n_remito="1234", n_factura="1234", 
            vencimiento=(datetime.datetime.now()+datetime.timedelta(30)).strftime("%d/%m/%Y"), 
            gtin="GTIN1", lote=datetime.datetime.now().strftime("%Y"),
            desde_numero_serial=int(time.time())-1, hasta_numero_serial=int(time.time())+1, 
            id_obra_social=None, id_evento=134,
            )
        print "Resultado", ws.Resultado
        print "CodigoTransaccion", ws.CodigoTransaccion
        print "Erroes", ws.Errores
        codigo_transaccion = ws.CodigoTransaccion
        print "Cancelando..."
        ws.SendCancelacTransacc(
            usuario='pruebasws', password='pruebasws',
            codigo_transaccion=codigo_transaccion)
        print "Resultado", ws.Resultado
        print "CodigoTransaccion", ws.CodigoTransaccion
        print "Errores", ws.Errores
    elif '--cancela' in sys.argv:
        ws.SendCancelacTransacc(*sys.argv[sys.argv.index("--cancela")+1:])
    elif '--confirma' in sys.argv:
        if '--loadxml' in sys.argv:
            ws.LoadTestXML("trazamed_confirma.xml")  # cargo respuesta
            ok = ws.SendConfirmaTransacc(usuario="pruebasws", password="pruebasws",
                                   p_ids_transac="1", f_operacion="31-12-2013")
            if not ok:
                raise RuntimeError(ws.Excepcion)
        ws.SendConfirmaTransacc(*sys.argv[sys.argv.index("--confirma")+1:])
    elif '--alerta' in sys.argv:
        ws.SendAlertaTransacc(*sys.argv[sys.argv.index("--alerta")+1:])
    elif '--consulta' in sys.argv:
        ws.GetTransaccionesNoConfirmadas(
                                *sys.argv[sys.argv.index("--consulta")+1:]
                                #usuario="pruebasws", password="pruebasws", 
                                #p_id_transaccion_global="1234", 
                                #id_agente_informador="1", 
                                #id_agente_origen="1", 
                                #id_agente_destino="1", 
                                #id_medicamento="1", 
                                #id_evento="1", 
                                #fecha_desde_op="01/01/2013", 
                                #fecha_hasta_op="31/12/2013", 
                                #fecha_desde_t="01/01/2013", 
                                #fecha_hasta_t="31/12/2013", 
                                #fecha_desde_v="01/04/2013", 
                                #fecha_hasta_v="30/04/2013", 
                                #n_factura=5, n_remito=6,
                                #estado=1
                                )
        print "CantPaginas", ws.CantPaginas
        print "HayError", ws.HayError
        #print "TransaccionPlainWS", ws.TransaccionPlainWS
        # parametros comunes de salida (columnas de la tabla):
        claves = ['_gtin', '_lote', '_numero_serial',
                  '_nombre',
                  '_id_transaccion', '_estado', '_f_transaccion', '_f_evento',
                  '_d_evento',
                  '_gln_origen', '_gln_destino',
                  '_razon_social_origen', '_razon_social_destino',
                  '_n_remito', '_n_factura',
                  ]
        # encabezado de la tabla:
        print "||", "||".join(["%s" % clave for clave in claves]), "||"
        # recorro los datos devueltos (TransaccionPlainWS):
        while ws.LeerTransaccion():     
            for clave in claves:
                print "||", ws.GetParametro(clave),         # imprimo cada fila
            print "||"
    else:
        ws.SendMedicamentos(*sys.argv[1:])
    print "|Resultado %5s|CodigoTransaccion %10s|Errores|%s|" % (
            ws.Resultado,
            ws.CodigoTransaccion,
            '|'.join(ws.Errores),
            )
    if ws.Excepcion:
        print ws.Traceback

# busco el directorio de instalaci�n (global para que no cambie si usan otra dll)
if not hasattr(sys, "frozen"): 
    basepath = __file__
elif sys.frozen=='dll':
    import win32api
    basepath = win32api.GetModuleFileName(sys.frozendllhandle)
else:
    basepath = sys.executable
INSTALL_DIR = os.path.dirname(os.path.abspath(basepath))


if __name__ == '__main__':

    # ajusto el encoding por defecto (si se redirije la salida)
    if sys.stdout.encoding is None:
        import codecs, locale
        sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout,"replace");
        sys.stderr = codecs.getwriter(locale.getpreferredencoding())(sys.stderr,"replace");

    if '--register' in sys.argv or '--unregister' in sys.argv:
        import pythoncom
        if TYPELIB: 
            if '--register' in sys.argv:
                tlb = os.path.abspath(os.path.join(INSTALL_DIR, "trazamed.tlb"))
                print "Registering %s" % (tlb,)
                tli=pythoncom.LoadTypeLib(tlb)
                pythoncom.RegisterTypeLib(tli, tlb)
            elif '--unregister' in sys.argv:
                k = TrazaMed
                pythoncom.UnRegisterTypeLib(k._typelib_guid_, 
                                            k._typelib_version_[0], 
                                            k._typelib_version_[1], 
                                            0, 
                                            pythoncom.SYS_WIN32)
                print "Unregistered typelib"
        import win32com.server.register
        win32com.server.register.UseCommandLine(TrazaMed)
    elif "/Automate" in sys.argv:
        # MS seems to like /automate to run the class factories.
        import win32com.server.localserver
        #win32com.server.localserver.main()
        # start the server.
        win32com.server.localserver.serve([TrazaMed._reg_clsid_])
    else:
        main()
