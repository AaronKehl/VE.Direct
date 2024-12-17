#!/usr/bin/env python3
#******************************** Dependencies *********************************
import serial
import time
import random
#*******************************************************************************
#==================================== Intro ====================================
    # Aaron Kehl
    # USACE - ERDC - CRREL
    # Summer 2024
    #
    # VE.Direct Hex BMV Protocol class for victron battery monitors/shunts.
#-------------------------------------------------------------------------------
#----------------------------------- License -----------------------------------
    # Copyright 2024 Aaron Kehl
    #
    # Permission is hereby granted, free of charge, to any person obtaining a 
    # copy of this software and associated documentation files (the “Software”), 
    # to deal in the Software without restriction, including without limitation 
    # the rights to use, copy, modify, merge, publish, distribute, sublicense, 
    # and/or sell copies of the Software, and to permit persons to whom the 
    # Software is furnished to do so, subject to the following conditions:
    #
    # The above copyright notice and this permission notice shall be 
    # included in all copies or substantial portions of the Software.
    #
    # THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, 
    # EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF 
    # MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
    # IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY 
    # CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, 
    # TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE 
    # SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#-------------------------------------------------------------------------------
#===============================================================================

#=================================== Globals ===================================
#---------------------------------- Vairables ----------------------------------
#-------------------------------------------------------------------------------
#---------------------------------- Constants ----------------------------------
#-------------------------------------------------------------------------------
#===============================================================================

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< BMVHex Class >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#******************************** initialize ***********************************
class bmvhex(object):
    """ Serial Python Interfacing Class for VE.Direct solar charge controller 
    """
    def __init__( self, port ):
        """ To Be Determined..."""
        self._port = port
        self._address = '0x204'
        self._baudrate = 19200
        self._timeout = 1
        self._ERROR_VAL = -9999
        self._DEBUG = False
        self._DESCRIPTIVE = False
        self._PREFIX = "[VE_DIR]: "

    def __del__( self ):
        """ To Be Determined..."""
        pass

    @property 
    def port( self ): return( self._port )
    @port.setter
    def port( self, value ): self._port = value 

    @property
    def address( self ): return( self._address )
    @address.setter
    def address( self, value ): self._address = value 

    @property
    def baudrate( self ): return( self._baudrate )
    @baudrate.setter
    def baudrate( self, value ): self._baudrate = value 

    @property
    def timeout( self ): return( self._timeout )
    @timeout.setter
    def timeout( self, value ): self._timeout = value

    @property
    def DEBUG( self ): return( self._DEBUG )
    @DEBUG.setter
    def DEBUG( self, value ): self._DEBUG = value 

    @property
    def DESCRIPTIVE( self ): return( self._DESCRIPTIVE )
    @DESCRIPTIVE.setter
    def DESCRIPTIVE( self, value ): self._DESCRIPTIVE = value     
    
    @property
    def ERROR_VAL( self ): return( self._ERROR_VAL )
    @ERROR_VAL.setter
    def ERROR_VAL( self, value ): self._ERROR_VAL = value 
    
    @property
    def PREFIX( self ): return( self._PREFIX )
#*******************************************************************************

#============================== Utility Functions ==============================
#---------------------------------- twos_comp ----------------------------------
    def _twos_comp( self, value, bits ):
        """ Small subroutine for computing twos complement with 'custom' numbers of bits.
            Step 1. Determine sign bit (leading bit value) based on number of bits
            Step 2. If leading bit is 1, convert to a signed integer.  If 0, do nothing.
            Step 3. Return the 2s complement value to the caller.
        """
        if( value & ( 1 << ( bits - 1 ) ) ):
            value = value - ( 1 << bits )
        return value
#-------------------------------------------------------------------------------
#--------------------------------- crc_calc ------------------------------------
    def _crc_calc( self, data ):
        sum = 0 

        for x in data:
            sum += self._twos_comp( x, 8 )
        crc_dec = 85 - sum

        if crc_dec >= -255 and crc_dec < 0: crc_dec = crc_dec + 256
        elif crc_dec >= -65535 and crc_dec < 0: crc_dec = crc_dec + 65536
        elif crc_dec >= -1677215 and crc_dec < 0: crc_dec = crc_dec + 1677216
        elif crc_dec >= -4294967295 and crc_dec <0: crc_dec = crc_dec + 4294967296

        if crc_dec >= 0 and crc_dec <= 255:
            crc = crc_dec.to_bytes( 1, byteorder='big', signed=False )
        elif crc_dec >= 256 and crc_dec <= 65535:
            crc = crc_dec.to_bytes( 2, byteorder='big', signed=False )
        elif crc_dec >= 65536 and crc_dec <= 16777215:
            crc = crc_dec.to_bytes( 3, byteorder='big', signed=False )
        else:
            try:
                crc = crc_dec.to_bytes( 4, byteorder='big', signed=False )
            except:
                crc = self.ERROR_VAL

        return crc
#-------------------------------------------------------------------------------
#------------------------------ two_bits_array ---------------------------------
    def _two_bits_array( self, value, bits ):
        """ Converts an integer to an array of bit pairs.
        """
        # convert integer value into
        two_bit_array = []
        bit_pairs = int( bits / 2 )

        for i in range( bit_pairs ):
            value_of_hi_bit = value & ( 1 << ( bits - 1 - ( i * 2 ) ) )
            value_of_lo_bit = value & ( 1 << ( bits - 1 - ( i * 2 + 1) ) )
            if value_of_hi_bit >= 1:
                value_of_hi_bit = 1
            if value_of_lo_bit >= 1:
                value_of_lo_bit = 1
            two_bit_array.append( "0b" + str( value_of_hi_bit ) + str( value_of_lo_bit ) )
        
        return two_bit_array
#-------------------------------------------------------------------------------
#--------------------------------- bit_array -----------------------------------
    def _bit_array( self, value, bits ):
        """ Converts an integer into an array of bit values.
        """
        bit_array = []
        for i in range( bits ):
            value_of_bit = ( value & ( 1 << ( bits - i - 1 ) ) )
            if value_of_bit >= 1:
                bit_array.append( "0b1" )
            elif value_of_bit == 0:
                bit_array.append( "0b0" )
            else:
                bit_array.append( self.ERROR_VAL )
        
        return bit_array
#-------------------------------------------------------------------------------
#----------------------------------- to_hex ------------------------------------
    def _to_hex( self, data ):
        """ Converts byte message into a string of hex values.
        """
        hex_string = ""
        for x in data:
            raw_hex = hex( x ).upper()
            if len( raw_hex ) == 3: hex_string += "0x0" + raw_hex[2:] + " "
            elif len( raw_hex ) == 4:hex_string += "0x" + hex( x )[2:].upper() + " "
            else: return self.ERROR_VAL 
        return hex_string
#-------------------------------------------------------------------------------
#--------------------------------- from_ascii ----------------------------------
    def _from_ascii( self, data ):
        char = chr( int.from_bytes( data ) )
        if   char == "1": return_value = 1
        elif char == "2": return_value = 2
        elif char == "3": return_value = 3
        elif char == "4": return_value = 4
        elif char == "5": return_value = 5
        elif char == "6": return_value = 6
        elif char == "7": return_value = 7
        elif char == "8": return_value = 8
        elif char == "9": return_value = 9
        elif char == "A": return_value = 10
        elif char == "B": return_value = 11
        elif char == "C": return_value = 12
        elif char == "D": return_value = 13
        elif char == "E": return_value = 14
        elif char == "F": return_value = 15
        else: return_value = 0
        return return_value 
#-------------------------------------------------------------------------------
#------------------------------- flip_endianness -------------------------------
    def _flip( self, data ):
        try: 
            return_value = bytes()
            decimal = int.from_bytes( data, byteorder='big', signed=True )
            return_value = decimal.to_bytes( len( data ), byteorder='little', signed=True )
        except:
            print( self._PREFIX + "Issue flipping the bytes endianness " + str( data ) + "." )
            return self.ERROR_VAL
        return return_value 
#-------------------------------------------------------------------------------
#-------------------------------- bytes_to_asc ---------------------------------
    def _bytes_to_ascii_bytes( self, data ):
        return_value = ""
        for x in data:
            decimal = int( x )
            if decimal < 16:
                return_value = return_value + "0" + hex(decimal)[2:].upper()
            else:
                return_value = return_value + hex(decimal)[2:].upper()       
        return str.encode( return_value, 'utf-8' ) 
#-------------------------------------------------------------------------------
#-------------------------------- asc_to_bytes ---------------------------------
    def _ascii_bytes_to_bytes( self, data ):
        return_value = bytes()
        if len( data ) == 1: 
            decimal = self._from_ascii( data )
            return_value = return_value + decimal.to_bytes( 1, byteorder='big', signed=True )
        else: 
            for i in range( 0, len( data ), 2 ):
                hi_byte = self._from_ascii( data[i:i+1] )
                lo_byte = self._from_ascii( data[i+1:i+2] )
                new_num = ( ( hi_byte << 4 ) | lo_byte ) 
                return_value = return_value + new_num.to_bytes( 1, byteorder='big', signed=False )
        return return_value 
#-------------------------------------------------------------------------------
#------------------------------- hex_adj_for_crc -------------------------------
    def _hex_adj_for_crc( self, data ):
        return_value = bytes()
        for x in data:
            dec = self._twos_comp( x, 8 ) - 48
            return_value = return_value + dec.to_bytes( 1, byteorder='big',signed=True)
        return return_value 
#-------------------------------------------------------------------------------
#=========================== End Utility Functions =============================

#=============================== COM Functions =================================
#-------------------------------- close_port -----------------------------------
    def _close_port( self, serial_device ):
        serial_device.close()
#-------------------------------------------------------------------------------
#--------------------------------- open_port -----------------------------------
    def _open_port( self ):
        serial_device = serial.Serial( self.port, baudrate=self.baudrate, timeout=self.timeout )
        return serial_device
#-------------------------------------------------------------------------------
#--------------------------------- send_cmd ------------------------------------
    def _send_cmd( self, cmd ):
        tx_msg = bytes()
        tx_cmd = ( ":" + cmd ).encode( "utf-8" )
        crc = self._crc_calc( self._ascii_bytes_to_bytes( cmd.encode( "utf-8" ) ) )
        tx_crc = self._bytes_to_ascii_bytes( crc )
        tx_nln = str.encode( "\n", 'utf-8' )
        tx_msg = tx_cmd + tx_crc + tx_nln
        return_value = self.ERROR_VAL

        if self.DEBUG:
            print( self._PREFIX + "T(" + str( len( tx_msg ) ) + " Bytes): " + self._to_hex( tx_msg ) )
            print( self._PREFIX + "Tx_Msg = " + tx_msg.decode( 'utf-8' ) )

        # Write binary data to port and read the respnse if it's availabe.
        try: 
            serial_device = self._open_port() 
            n_tries = 5
            for i in range( n_tries ):
                rx_msg = bytes()

                bytes_written = serial_device.write( tx_msg )
                if bytes_written == len( tx_msg ):
                    if cmd == "6": 
                        rx_msg = "RESTART"
                        break
                    # wait for a response to be available, 2s
                    count = 0
                    while not serial_device.in_waiting and count < 100:
                        count = count + 1
                        time.sleep( 0.02 )
                        
                    # now that there is data waiting to come in, read up to 1000 bytes.
                    count = 0
                    while serial_device.in_waiting > 0 and count < 1000:
                        rx_msg = rx_msg + serial_device.read()
                        count = count + 1
                        time.sleep( 0.002 )

                    if  rx_msg.find( b':A' ) == -1 and rx_msg != 'b\xE8' and \
                        rx_msg.find( b'\t' ) == -1 and len( rx_msg ) == 8:
                        # we have a good return that is not the asynch message
                        break
                    else:
                        # sometimes we fail due to the heartbeat
                        # coming from the ve.device, this delay lets
                        # it finish before we try to poll the device again
                        if i + 1 == n_tries:
                            print( self._PREFIX + "Max attempts to send cmd reached." )
                            return self.ERROR_VAL
                        else:
                            rnd = random.randrange( 1, 1025 )
                            dur = ( ( i + 1 ) / n_tries ) + ( rnd / 1024 )
                            serial_device.send_break( duration=dur )
                            serial_device.reset_input_buffer()
                            serial_device.reset_output_buffer()

        except:
            print( self._PREFIX + "Unable to reach device!" )
            try: self._close_port( serial_device )
            except: pass
            return self.ERROR_VAL

        self._close_port( serial_device )
            
        if self.DEBUG and cmd != "6":
            print( self._PREFIX + "R(" + str( len( rx_msg ) ) + " Bytes): " + self._to_hex( rx_msg ) )
            print( self._PREFIX + "Rx_Msg = " + rx_msg.decode( 'utf-8' ) )

        # Start parsing out the response, if these fields don't exist return an error.
        if cmd != "6":
            try: 
                if cmd == "1" and rx_msg[2:4] == ":5".encode( "utf-8" ): rx_msg = rx_msg[2:]
                if cmd == "3" and rx_msg[2:4] == ":1".encode( "utf-8" ): rx_msg = rx_msg[2:]
                if cmd == "4" and rx_msg[2:4] == ":1".ecnode( "utf-8" ): rx_msg = rx_msg[2:]
                if rx_msg[2:4] == tx_cmd: rx_msg = rx_msg[2:]
                rx_cmd = rx_msg[:2]
                rx_dat = rx_msg[2:6]
                rx_crc = rx_msg[-3:-1]
                rx_nln = rx_msg[-1:]
                
                # update data and crc to bytes from ascii bytes
                rx_dat = self._ascii_bytes_to_bytes( rx_dat )
                rx_dat = self._flip( rx_dat )
                rx_crc = self._ascii_bytes_to_bytes( rx_crc )

                if self.DEBUG: 
                    print( self._PREFIX + "rx_cmd = " + self._to_hex( rx_cmd ) )
                    print( self._PREFIX + "rx_dat = " + self._to_hex( rx_dat ) )
                    print( self._PREFIX + "rx_crc = " + self._to_hex( rx_crc ) )
                    print( self._PREFIX + "rx_nln = " + self._to_hex( rx_nln ) + "\n" )

                if rx_nln != tx_nln:
                    print( self._PREFIX + "End of command line character not detected! rx_nln = " + str( rx_nln ) + ", tx_nln = " + str( tx_nln ) )
                    return self.ERROR_VAL 

                 # calculate the crc we should be getting back if we've made it this far.
                rx_crc_msg = bytes() 
                rx_crc_msg = self._ascii_bytes_to_bytes( rx_cmd[1:] )
                rx_crc_msg = rx_crc_msg + rx_dat
                crc = self._crc_calc( rx_crc_msg )[-1:]

                # now that we have the crc we can verify we got a good response from the insturment
                if rx_crc != crc:
                    print( self._PREFIX + "CRC does not match! " + "rx_crc = " + self._to_hex( rx_crc ) + ", crc = " + self._to_hex( crc ) ) 
                    return self.ERROR_VAL
                
                return_value = int.from_bytes( rx_dat, byteorder='big', signed=True ) 
            except:
                print( self._PREFIX + "Invalid response format." )
                return self.ERROR_VAL
        
        return return_value 
#------------------------------------------------------------------------------- 
#----------------------------------- read --------------------------------------
    def _read( self, data_len, reg_addr, format='int' ):
        # make our initial adjustments, ve.direct flips endianness of reg
        reg_addr = self._flip( reg_addr )

        # need to keep as bytes to compute CRC relatively easily.
        tx_msg = bytes()
        tx_msg = b'\x07'
        tx_msg = tx_msg + reg_addr
        tx_msg = tx_msg + b'\x00'
        crc = self._crc_calc( tx_msg )
        
        # now that we have the crc value, let's adjust it to what victron
        # device wants to see.
        tx_msg = bytes()
        tx_cmd = str.encode( ":7", 'utf-8' )
        tx_reg = self._bytes_to_ascii_bytes( reg_addr )
        tx_flg = self._bytes_to_ascii_bytes( b'\x00' )
        tx_crc = self._bytes_to_ascii_bytes( crc )
        tx_nln = str.encode( "\n", 'utf-8' )
        tx_msg = tx_cmd + tx_reg + tx_flg + tx_crc + tx_nln
        return_value = self.ERROR_VAL

        if self.DEBUG:
            print( self._PREFIX + "T(" + str( len( tx_msg ) ) + " Bytes): " + self._to_hex( tx_msg ) )
            print( self._PREFIX + "Tx_Msg = " + tx_msg.decode( 'utf-8' ) )
            print( self._PREFIX + "tx_cmd = " + self._to_hex( tx_cmd ) )
            print( self._PREFIX + "tx_reg = " + self._to_hex( tx_reg ) )
            print( self._PREFIX + "tx_flg = " + self._to_hex( tx_flg ) )
            print( self._PREFIX + "tx_crc = " + self._to_hex( tx_crc ) )
            print( self._PREFIX + "tx_nln = " + self._to_hex( tx_nln ) + "\n" )

        # Write binary data to port and read the response if it's availabe.
        try: 
            serial_device = self._open_port() 
            n_tries = 5
            for i in range( n_tries ):
                rx_msg = bytes()

                bytes_written = serial_device.write( tx_msg )
                if bytes_written == len( tx_msg ):
                    # wait for a response to be available, 2s
                    count = 0
                    while not serial_device.in_waiting and count < 100:
                        count = count + 1
                        time.sleep( 0.02 )
                        
                    # now that there is data waiting to come in, read up to 1000 bytes.
                    count = 0
                    while serial_device.in_waiting > 0 and count < 1000:
                        rx_msg = rx_msg + serial_device.read()
                        count = count + 1
                        time.sleep( 0.002 )
                    
                    rx_len = len( rx_msg )
                    if rx_len <= bytes_written + data_len*2 + 2 and \
                        rx_msg.find( b':A' ) == -1 and rx_msg != 'b\xE8' and \
                        rx_msg.find( b'\t' ) == -1 and rx_len >= bytes_written:
                        # we have a good return that is not the asynch message
                        break
                    else:
                        # sometimes we fail due to the heartbeat
                        # coming from the ve.device, this delay lets
                        # it finish before we try to poll the device again
                        if i + 1 == n_tries: 
                            print( self._PREFIX + "Max attempts to read reached." )
                            return self.ERROR_VAL
                        else: 
                            rnd = random.randrange( 1, 1025 )
                            dur = ( ( i + 1 ) / n_tries ) + ( rnd / 1024 )
                            serial_device.send_break( duration=dur )
                            serial_device.reset_input_buffer()
                            serial_device.reset_output_buffer()

        except:
            print( self._PREFIX + "Unable to reach device!" )
            try: self._close_port( serial_device )
            except: pass
            return self.ERROR_VAL

        self._close_port( serial_device )
            
        if self.DEBUG:
            print( self._PREFIX + "R(" + str( len( rx_msg ) ) + " Bytes): " + self._to_hex( rx_msg ) )
            print( self._PREFIX + "Rx_Msg = " + rx_msg.decode( 'utf-8' ) )

        # Start parsing out the response, if these fields don't exist return an error.
        try: 
            if rx_msg[2:4] == tx_cmd: rx_msg = rx_msg[2:]
            rx_cmd = rx_msg[:2]
            rx_reg = rx_msg[2:6]
            rx_flg = rx_msg[6:8]
            rx_dat = rx_msg[8:-3]
            rx_crc = rx_msg[-3:-1]
            rx_nln = rx_msg[-1:]
            
            # update data and crc to bytes from ascii bytes
            rx_dat = self._ascii_bytes_to_bytes( rx_dat )
            if format == 'int' or format == 'int_ovvr': rx_dat = self._flip( rx_dat )
            rx_crc = self._ascii_bytes_to_bytes( rx_crc )

            if self.DEBUG: 
                print( self._PREFIX + "rx_cmd = " + self._to_hex( rx_cmd ) )
                print( self._PREFIX + "rx_reg = " + self._to_hex( rx_reg ) )
                print( self._PREFIX + "rx_flg = " + self._to_hex( rx_flg ) )
                print( self._PREFIX + "rx_dat = " + self._to_hex( rx_dat ) )
                print( self._PREFIX + "rx_crc = " + self._to_hex( rx_crc ) )
                print( self._PREFIX + "rx_nln = " + self._to_hex( rx_nln ) + "\n" )

        except:
            print( self._PREFIX + "Invalid response format." )
            return self.ERROR_VAL
            
        # go through first three sets of data and the last
        if rx_cmd != tx_cmd: 
            print( self._PREFIX + "Response command does not match! rx_cmd = " + str( rx_cmd ) + ", cmd = " + str( tx_cmd ) )
            return self.ERROR_VAL
        elif rx_reg != tx_reg:
            print( self._PREFIX + "Response address does not match! rx_reg = " + str( rx_reg ) + ", reg = " + str( tx_reg ) )
            return self.ERROR_VAL
        elif rx_flg != tx_flg:
            print( self._PREFIX + "Response flag does not match! rx_flg = " + str( rx_flg ) + ", flg = " + str( tx_flg ) )
            return self.ERROR_VAL
        elif rx_nln != tx_nln:
            print( self._PREFIX + "End of command line character not detected! rx_nln = " + str( rx_nln ) + ", tx_nln = " + str( tx_nln ) )
            return self.ERROR_VAL 
            
        # calculate the crc we should be getting back if we've made it this far.
        rx_crc_msg = bytes() 
        rx_crc_msg = self._ascii_bytes_to_bytes( rx_cmd[1:] )
        rx_crc_msg = rx_crc_msg + self._ascii_bytes_to_bytes( rx_reg )
        rx_crc_msg = rx_crc_msg + self._ascii_bytes_to_bytes( rx_flg )
        if format == 'int' or format == 'b': rx_crc_msg = rx_crc_msg + rx_dat
        if format == 'str' or format == 'str_ovvr': 
            rx_crc_msg = rx_crc_msg + self._hex_adj_for_crc( rx_dat )
        crc = self._crc_calc( rx_crc_msg )[-1:]

        # now that we have the crc we can verify we got a good response from the insturment
        if rx_crc != crc:
            print( self._PREFIX + "CRC does not match! " + "rx_crc = " + self._to_hex( rx_crc ) + ", crc = " + self._to_hex( crc ) ) 
            if format.find( "ovvr" ) == -1: return self.ERROR_VAL
        
        if format == 'int' or format == 'int_ovvr':
            return_value = int.from_bytes( rx_dat, byteorder='big', signed=True )
        elif format == 'b' or format =='b_ovvr':
            return_value = rx_dat
        elif format == 'str':
            return_value = rx_dat.decode( 'utf-8' )
        elif format == 'str_ovvr':
            return_value = rx_dat.decode( 'utf-8' )[:-2]
        else:
            print( self._PREFIX + "Invalid format selection, choices are int, b, str. You specified " + str( format ) + "..." )
            return self.ERROR_VAL
        
        return return_value
#-------------------------------------------------------------------------------
#----------------------------------- write -------------------------------------
    def _write( self, value, data_len, reg_addr, format='int' ):
        # make our initial adjustments, ve.direct flips endianness of reg
        reg_addr = self._flip( reg_addr )

        # need to keep as bytes to compute CRC relatively easily.
        tx_msg = bytes()
        tx_msg = b'\x08'
        tx_msg = tx_msg + reg_addr
        tx_msg = tx_msg + b'\x00'
        tx_msg = tx_msg + value 
        crc = self._crc_calc( tx_msg )
        
        # now that we have the crc value, let's adjust it to what victron
        # device wants to see.
        tx_msg = bytes()
        tx_cmd = str.encode( ":8", 'utf-8' )
        tx_reg = self._bytes_to_ascii_bytes( reg_addr )
        tx_flg = self._bytes_to_ascii_bytes( b'\x00' )
        tx_val = self._bytes_to_ascii_bytes( value )
        tx_crc = self._bytes_to_ascii_bytes( crc )
        tx_nln = str.encode( "\n", 'utf-8' )
        tx_msg = tx_cmd + tx_reg + tx_flg + tx_val + tx_crc + tx_nln
        return_value = self.ERROR_VAL

        if self.DEBUG:
            print( self._PREFIX + "T(" + str( len( tx_msg ) ) + " Bytes): " + self._to_hex( tx_msg ) )
            print( self._PREFIX + "Tx_Msg = " + tx_msg.decode( 'utf-8' ) )
            print( self._PREFIX + "tx_cmd = " + self._to_hex( tx_cmd ) )
            print( self._PREFIX + "tx_reg = " + self._to_hex( tx_reg ) )
            print( self._PREFIX + "tx_flg = " + self._to_hex( tx_flg ) )
            print( self._PREFIX + "tx_val = " + self._to_hex( tx_val ) )
            print( self._PREFIX + "tx_crc = " + self._to_hex( tx_crc ) )
            print( self._PREFIX + "tx_nln = " + self._to_hex( tx_nln ) + "\n" )

        # Write binary data to port and read the respnse if it's availabe.
        try: 
            serial_device = self._open_port() 
            n_tries = 5
            for i in range( n_tries ):
                rx_msg = bytes()

                bytes_written = serial_device.write( tx_msg )
                if bytes_written == len( tx_msg ):
                    # wait for a response to be available, 2s
                    count = 0
                    while not serial_device.in_waiting and count < 100:
                        count = count + 1
                        time.sleep( 0.02 )
                        
                    # now that there is data waiting to come in, read up to 1000 bytes.
                    count = 0
                    while serial_device.in_waiting > 0 and count < 1000:
                        rx_msg = rx_msg + serial_device.read()
                        count = count + 1
                        time.sleep( 0.002 )

                    rx_len = len( rx_msg )
                    if rx_len <= bytes_written + data_len*2 + 2 and \
                        rx_msg.find( b':A' ) == -1 and rx_msg != 'b\xE8' and \
                        rx_msg.find( b'\t' ) == -1 and rx_len >= bytes_written:
                        break
                    else:
                        # sometimes we fail due to the heartbeat
                        # coming from the ve.device, this delay lets
                        # it finish before we try to poll the device again
                        if i + 1 == n_tries: 
                            print( self._PREFIX + "Max attempts to write reached." )
                            return self.ERROR_VAL
                        else: 
                            rnd = random.randrange( 1, 1025 )
                            dur = ( ( i + 1 ) / n_tries ) + ( rnd / 1024 )
                            serial_device.send_break( duration=dur )
                            serial_device.reset_input_buffer()
                            serial_device.reset_output_buffer()

        except:
            print( self._PREFIX + "Unable to reach device!" )
            try: self._close_port( serial_device )
            except: pass
            return self.ERROR_VAL

        self._close_port( serial_device )
            
        if self.DEBUG:
            print( self._PREFIX + "R(" + str( len( rx_msg ) ) + " Bytes): " + self._to_hex( rx_msg ) )
            print( self._PREFIX + "Rx_Msg = " + rx_msg.decode( 'utf-8' ) )

        if not rx_msg == tx_msg:
            print( self._PREFIX + "Unable to update parameter to provided input." )
        
        # Start parsing out the response, if these fields don't exist return an error.
        try: 
            if rx_msg[2:4] == tx_cmd: rx_msg = rx_msg[2:]
            rx_cmd = rx_msg[:2]
            rx_reg = rx_msg[2:6]
            rx_flg = rx_msg[6:8]
            rx_dat = rx_msg[8:-3]
            rx_crc = rx_msg[-3:-1]
            rx_nln = rx_msg[-1:]

            if self.DEBUG: 
                print( self._PREFIX + "rx_cmd = " + self._to_hex( rx_cmd ) )
                print( self._PREFIX + "rx_reg = " + self._to_hex( rx_reg ) )
                print( self._PREFIX + "rx_flg = " + self._to_hex( rx_flg ) )
                print( self._PREFIX + "rx_dat = " + self._to_hex( rx_dat ) )
                print( self._PREFIX + "rx_crc = " + self._to_hex( rx_crc ) )
                print( self._PREFIX + "rx_nln = " + self._to_hex( rx_nln ) + "\n" )

        except:
            print( self._PREFIX + "Invalid response format." )
            return self.ERROR_VAL
        
        # go through first three sets of data and the last
        if rx_cmd != tx_cmd: 
            print( self._PREFIX + "Response command does not match! rx_cmd = " + str( rx_cmd ) + ", cmd = " + str( tx_cmd ) )
            return self.ERROR_VAL
        elif rx_reg != tx_reg:
            print( self._PREFIX + "Response address does not match! rx_reg = " + str( rx_reg ) + ", reg = " + str( tx_reg ) )
            return self.ERROR_VAL
        elif rx_flg != tx_flg:
            print( self._PREFIX + "Response flag does not match! rx_flg = " + str( rx_flg ) + ", flg = " + str( tx_flg ) )
            return self.ERROR_VAL
        elif rx_crc != tx_crc:
            print( self._PREFIX + "CRC does not match! " + "rx_crc = " + self._to_hex( rx_crc ) + ", tx_crc = " + self._to_hex( tx_crc ) ) 
            return self.ERROR_VAL
        elif rx_nln != tx_nln:
            print( self._PREFIX + "End of command line character not detected! rx_nln = " + str( rx_nln ) + ", tx_nln = " + str( tx_nln ) )
            return self.ERROR_VAL 
        
        if format == 'int' or format == 'int_ovvr':
            return_value = int.from_bytes( rx_dat, byteorder='big', signed=True )
        elif format == 'b' or format =='b_ovvr':
            return_value = rx_dat
        elif format == 'str':
            return_value = rx_dat.decode( 'utf-8' )
        elif format == 'str_ovvr':
            return_value = rx_dat.decode( 'utf-8' )[:-2]
        else:
            print( self._PREFIX + "Invalid format selection, choices are int, b, str. You specified " + str( format ) + "..." )
            return self.ERROR_VAL
        
        return return_value
#-------------------------------------------------------------------------------
#---------------------------------- readall ------------------------------------
    @property
    def readall( self ):
        """ Just a function to listen to the com port for a bit..."""

        try:
            serial_device = self._open_port() 
        except:
            print( self._PREFIX + "Unable to reach device!" )
            return None
        
        listening = True 
        receive_message = bytes()
        count = 0
        while listening: 
            try: 
                bytestream = serial_device.read() 
                receive_message = receive_message + bytestream

                if bytestream == b'V':
                    if receive_message[-3:] == b'BMV' and count > 0:
                        print( self._PREFIX + "End of heartbeat detected..." )
                        receive_message = receive_message[:-3]
                        break
                    if receive_message[-3:] == b'BMV' and count == 0:
                        receive_message = receive_message[-3:]
                        count = count + 1
                    
            except KeyboardInterrupt: 
                print( self._PREFIX + "Exiting listen..." )
                break

        print( self._PREFIX + "" + str( receive_message ) )
        print( "[VE_DIR] R(" + str( len( receive_message ) ) + " Bytes): " + self._to_hex( receive_message ) )
        
        self._close_port( serial_device )
        return "Fin" 
#-------------------------------------------------------------------------------
#============================= End COM Functions ===============================

#================================ Properties ===================================
#----------------------------- Product Information -----------------------------
    @property 
    def pid( self ):
        reg_addr = b'\x01\x00'
        response = self._read( 4, reg_addr, 'b' )
        if response == b'\xFF': return self.ERROR_VAL
        else: return int.from_bytes( response, byteorder='little', signed=False )
    
    @property
    def product_revision( self ):
        reg_addr = b'\x01\x01'
        response = self._read( 3, reg_addr, 'b' )
        if response == b'\xFF': return self.ERROR_VAL
        else: return int.from_bytes( response, byteorder='little', signed=False )

    @property
    def serial_number( self ):
        reg_addr = b'\x01\x0A'
        return self._read( 64, reg_addr, 'b' ).decode( 'utf-8' )
    
    @property
    def model_name( self ):
        reg_addr = b'\x01\x0B'
        return self._read( 64, reg_addr, 'b' ).decode( 'utf-8' )
    
    @property
    def description( self ):
        reg_addr = b'\x01\x0C'
        return self._read( 40, reg_addr, 'b' ).decode( 'utf-8' )
    
    @property
    def device_uptime( self ):
        reg_addr = b'\x01\x20'
        response = self._read( 4, reg_addr, 'b' )
        return int.from_bytes( response, byteorder='little', signed=False )
    
    @property
    def bluetooth_capabilities( self ):
        reg_addr = b'\x01\x50'
        response = self._read( 4, reg_addr, 'b' )
        response = self._bit_array( int.from_bytes( response, byteorder='little', signed=False ), 32 )
        return response 
#---------------------------- End Product Information --------------------------

#--------------------------- Monitor Related Registers -------------------------
    @property 
    def main_voltage( self ):
        reg_addr = b'\xED\x8D'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response
        if response > 6000: return self.ERROR_VAL 
        else: return response / 100 
    
    @property
    def aux_voltage( self ):
        reg_addr = b'\xED\x7D'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response
        if response > 6000: return self.ERROR_VAL 
        else: return response / 100 

    @property 
    def current_twobyte( self ):
        reg_addr = b'\xED\x8F'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response
        else: return response / 10

    @property
    def current_fourbyte( self ):
        reg_addr = b'\xED\x8C'
        response = self._read( 4, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        else: return response / 1000

    @property
    def power( self ):
        reg_addr = b'\xED\x8E'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        else: return response

    @property
    def consumed_ah( self ):
        reg_addr = b'\xED\xFF'
        response = self._read( 4, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        else: return response / 10
    
    @property
    def soc( self ):
        reg_addr = b'\x0F\xFF'
        response = self._read( 2, reg_addr, 'b' )
        response = int.from_bytes( response, byteorder='little', signed=False )
        if response == self.ERROR_VAL: return response 
        if response < 0 or response > 10000: return self.ERROR_VAL 
        else: return response / 100

    @property
    def ttg( self ):
        reg_addr = b'\x0F\xFE'
        response = self._read( 2, reg_addr, 'b' )
        response = int.from_bytes( response, byteorder='little', signed=False )
        if response == self.ERROR_VAL: return response 
        else: return response 

    @property
    def temperature( self ):
        reg_addr = b'\xED\xEC'
        response = self._read( 2, reg_addr, 'b' )
        if response == b'\xFF\xFF': return self.ERROR_VAL
        else: return int.from_bytes( response, byteorder='little', signed=False ) / 100 - 273.15

    @property
    def mid_voltage( self ):
        reg_addr = b'\x03\x82'
        response = self._read( 2, reg_addr, 'b' )
        if response == b'\xFF\xFF': return self.ERROR_VAL
        else: return int.from_bytes( response, byteorder='little', signed=False ) / 100
    
    @property
    def mid_deviation( self ):
        reg_addr = b'\x03\x83'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response == 32767: return self.ERROR_VAL
        else: return response / 10

    @property
    def synch_state( self ):
        reg_addr = b'\xEE\xB6'
        response = self._read( 1, reg_addr, 'b' )
        if response == b'\xFF': return self.ERROR_VAL
        else: return int.from_bytes( response, byteorder='little', signed=False )
#-------------------------- End Monitor Related Registers ----------------------

#---------------------------- Historic Data Registers --------------------------
    @property 
    def deepest_discharge( self ):
        reg_addr = b'\x03\x00'
        response = self._read( 4, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        else: return response / 10

    @property
    def last_discharge_depth( self ):
        reg_addr = b'\x03\x01'
        response = self._read( 4, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        else: return response / 10 

    @property 
    def avg_discharge_depth( self ):
        reg_addr = b'\x03\x02'
        response = self._read( 4, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        else: return response / 10

    @property
    def cycles( self ):
        reg_addr = b'\x03\x03'
        response = self._read( 4, reg_addr, 'b' )
        return int.from_bytes( response, byteorder='little', signed=False )
    
    @property
    def full_discharges( self ):
        reg_addr = b'\x03\x04'
        response = self._read( 4, reg_addr, 'b' )
        return int.from_bytes( response, byteorder='little', signed=False )
    
    @property
    def cumulative_amphours( self ):
        reg_addr = b'\x03\x05'
        response = self._read( 4, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        else: return response / 10

    @property
    def min_voltage( self ):
        reg_addr = b'\x03\x06'
        response = self._read( 4, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        else: return response / 100 

    @property
    def max_voltage( self ):
        reg_addr = b'\x03\x07'
        response = self._read( 4, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        else: return response / 100 

    @property 
    def since_charge( self ):
        reg_addr = b'\x03\x08'
        response = self._read( 4, reg_addr, 'b' )
        if response == b'\xFF\xFF\xFF\xFF': return self.ERROR_VAL
        else: return int.from_bytes( response, byteorder='little', signed=False )

    @property
    def auto_syncs( self ):
        reg_addr = b'\x03\x09'
        response = self._read( 4, reg_addr, 'b' )
        if response == b'\xFF\xFF\xFF\xFF': return self.ERROR_VAL
        else: return int.from_bytes( response, byteorder='little', signed=False )

    @property
    def low_alarms( self ):
        reg_addr = b'\x03\x0A'
        response = self._read( 4, reg_addr, 'b' )
        if response == b'\xFF\xFF\xFF\xFF': return self.ERROR_VAL
        else: return int.from_bytes( response, byteorder='little', signed=False )

    @property
    def high_alarms( self ):
        reg_addr = b'\x03\x0B'
        response = self._read( 4, reg_addr, 'b' )
        if response == b'\xFF\xFF\xFF\xFF': return self.ERROR_VAL
        else: return int.from_bytes( response, byteorder='little', signed=False )

    @property
    def min_aux_voltage( self ):
        reg_addr = b'\x03\x0E'
        response = self._read( 4, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        else: return response / 100 

    @property
    def max_aux_voltage( self ):
        reg_addr = b'\x03\x0F'
        response = self._read( 4, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        else: return response / 100 

    @property
    def discharged_energy( self ):
        reg_addr = b'\x03\x10'
        response = self._read( 4, reg_addr, 'b' )
        if response == b'\xFF\xFF\xFF\xFF': return self.ERROR_VAL
        else: return int.from_bytes( response, byteorder='little', signed=False ) / 100

    @property
    def charged_energy( self ):
        reg_addr = b'\x03\x11'
        response = self._read( 4, reg_addr, 'b' )
        if response == b'\xFF\xFF\xFF\xFF': return self.ERROR_VAL
        else: return int.from_bytes( response, byteorder='little', signed=False ) / 100
#-------------------------- End Historic Data Registers ------------------------

#--------------------------- Monitor Settings Registers ------------------------
    @property
    def battery_capacity( self ):
        reg_addr = b'\x10\x00'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 1 and response <= 9999: return response
        else: return self.ERROR_VAL
    @battery_capacity.setter
    def battery_capacity( self, value ):
        reg_addr = b'\x10\x00'
        if value >= 1 and value <= 9999:
            value = int( value ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property 
    def charged_voltage( self ):
        reg_addr = b'\x10\x01'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 0 and response <= 950: return response / 10
        else: return self.ERROR_VAL
    @charged_voltage.setter
    def charged_voltage( self, value ):
        reg_addr = b'\x10\x01'
        if value >= 0 and value <= 95:
            value = int( value * 10 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def tail_current( self ):
        reg_addr = b'\x10\x02'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 5 and response <= 100: return response / 10 
        else: return self.ERROR_VAL 
    @tail_current.setter
    def tail_current( self, value ):
        reg_addr = b'\x10\x02'
        if value >= 0.5 and value <= 10: 
            value = int( value * 10 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property 
    def charged_detection_time( self ):
        reg_addr = b'\x10\x03'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 1 and response <= 50: return response 
        else: return self.ERROR_VAL 
    @charged_detection_time.setter
    def charged_detection_time( self, value ):
        reg_addr = b'\x10\x03'
        if value >= 1 and value <= 50:
            value = int( value ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def charge_efficiency( self ):
        reg_addr = b'\x10\x04'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 50 and response <= 99: return response 
        else: return self.ERROR_VAL
    @charge_efficiency.setter
    def charge_efficiency( self, value ):
        reg_addr = b'\x10\x04'
        if value >= 50 and value <= 99:
            value = int( value ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def peukert_coeff( self ):
        reg_addr = b'\x10\x05'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 100 and response <= 150: return response / 100
        else: return self.ERROR_VAL
    @peukert_coeff.setter
    def peukert_coeff( self, value ):
        reg_addr = b'\x10\x05'
        if value >= 1 and value <= 1.5:
            value = int( value * 100 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def current_threshold( self ):
        reg_addr = b'\x10\x06'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 0 and response <= 200: return response / 100
        else: return self.ERROR_VAL
    @current_threshold.setter
    def current_threshold( self, value ):
        reg_addr = b'\x10\x06'
        if value >= 0 and value <= 2:
            value = int( value * 100 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def ttg_delta_t( self ):
        reg_addr = b'\x10\x07'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 0 and response <= 12: return response 
        else: return self.ERROR_VAL
    @ttg_delta_t.setter
    def ttg_delta_t( self, value ):
        reg_addr = b'\x10\x07'
        if value >= 0 and value <= 12:
            value = int(value).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def discharge_floor( self ):
        reg_addr = b'\x10\x08'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 0 and response <= 990: return response / 10
        else: return self.ERROR_VAL 
    @discharge_floor.setter
    def discharge_floor( self, value ):
        reg_addr = b'\x10\x08'
        if value >= 0 and value <= 99:
            value = int( value * 10 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def relay_low_soc_clear( self ):
        reg_addr = b'\x10\x09'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 0 and response <= 990: return response / 10 
        else: return self.ERROR_VAL
    @relay_low_soc_clear.setter
    def relay_low_soc_clear( self, value ):
        reg_addr = b'\x10\x09'
        if value >= 0 and value <= 99:
            value = int( value * 10 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def user_current_zero( self ):
        reg_addr = b'\x10\x34' #read-only
        response = self._read( 2, reg_addr, 'int' )
        return response 
    @user_current_zero.setter
    def user_current_zero( self, value ):
        reg_addr = b'\x10\x29' #write-only
        value = b'\x00\x00'
        print( self.PREFIX + "input ignored, current value set as zero point." )
        self._write( value, 2, reg_addr, 'int' )
#----------------------- End Monitor Settings Registers ------------------------

#-------------------------------- Alarm Settings -------------------------------
    @property 
    def alarm_buzzer( self ):
        reg_addr = b'\xEE\xFC'
        response = self._read( 1, reg_addr, 'int' )
        if response == 0 or response == 1: return response 
        else: return self.ERROR_VAL
    @alarm_buzzer.setter 
    def alarm_buzzer( self, value ):
        reg_addr = b'\xEE\xFC'
        if value == 0 or value == 1:
            value = value.to_bytes( 1, byteorder='little', signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property
    def alarm_low_voltage( self ):
        reg_addr = b'\x03\x20'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 0 and response <= 950: return response / 10 
        else: return self.ERROR_VAL
    @alarm_low_voltage.setter
    def alarm_low_voltage( self, value ):
        reg_addr = b'\x03\x20'
        if value >= 0 and value <= 95: 
            value = int( value * 10 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def alarm_low_voltage_clear( self ):
        reg_addr = b'\x03\x21'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 0 and response <= 950: return response / 10 
        else: return self.ERROR_VAL
    @alarm_low_voltage_clear.setter
    def alarm_low_voltage_clear( self, value ):
        reg_addr = b'\x03\x21'
        if value >= 0 and value <= 95: 
            value = int( value * 10 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )
    
    @property
    def alarm_high_voltage( self ):
        reg_addr = b'\x03\x22'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 0 and response <= 950: return response / 10 
        else: return self.ERROR_VAL
    @alarm_high_voltage.setter
    def alarm_high_voltage( self, value ):
        reg_addr = b'\x03\x22'
        if value >= 0 and value <= 95: 
            value = int( value * 10 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )    

    @property
    def alarm_high_voltage_clear( self ):
        reg_addr = b'\x03\x23'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 0 and response <= 950: return response / 10 
        else: return self.ERROR_VAL
    @alarm_high_voltage_clear.setter
    def alarm_high_voltage_clear( self, value ):
        reg_addr = b'\x03\x23'
        if value >= 0 and value <= 95: 
            value = int( value * 10 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def alarm_low_starter( self ):
        reg_addr = b'\x03\x24'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 0 and response <= 950: return response / 10 
        else: return self.ERROR_VAL
    @alarm_low_starter.setter
    def alarm_low_starter( self, value ):
        reg_addr = b'\x03\x24'
        if value >= 0 and value <= 95: 
            value = int( value * 10 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def alarm_low_starter_clear( self ):
        reg_addr = b'\x03\x25'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 0 and response <= 950: return response / 10 
        else: return self.ERROR_VAL
    @alarm_low_starter_clear.setter
    def alarm_low_starter_clear( self, value ):
        reg_addr = b'\x03\x25'
        if value >= 0 and value <= 95: 
            value = int( value * 10 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def alarm_high_starter( self ):
        reg_addr = b'\x03\x26'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 0 and response <= 950: return response / 10 
        else: return self.ERROR_VAL
    @alarm_high_starter.setter
    def alarm_high_starter( self, value ):
        reg_addr = b'\x03\x26'
        if value >= 0 and value <= 95: 
            value = int( value * 10 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def alarm_high_starter_clear( self ):
        reg_addr = b'\x03\x27'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 0 and response <= 950: return response / 10 
        else: return self.ERROR_VAL
    @alarm_high_starter_clear.setter
    def alarm_high_starter_clear( self, value ):
        reg_addr = b'\x03\x27'
        if value >= 0 and value <= 95: 
            value = int( value * 10 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )
    
    @property
    def alarm_low_soc( self ):
        reg_addr = b'\x03\x28'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 0 and response <= 990: return response / 10
        else: return self.ERROR_VAL
    @alarm_low_soc.setter
    def alarm_low_soc( self, value ):
        reg_addr = b'\x03\x28'
        if value >= 0 and value <= 99:
            value = int( value * 10 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def alarm_low_soc_clear( self ):
        reg_addr = b'\x03\x29'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 0 and response <= 990: return response / 10
        else: return self.ERROR_VAL
    @alarm_low_soc_clear.setter
    def alarm_low_soc_clear( self, value ):
        reg_addr = b'\x03\x29'
        if value >= 0 and value <= 99:
            value = int( value * 10 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def alarm_low_temp( self ):
        reg_addr = b'\x03\x2A'
        response = self._read( 2, reg_addr, 'int' )
        if response == 0: return self.ERROR_VAL
        if response >= 17400 and response <= 37200: return response / 100 - 273.15
        else: return self.ERROR_VAL
    @alarm_low_temp.setter
    def alarm_low_temp( self, value ):
        reg_addr = b'\x03\x2A'
        if value >= -99.15 and value <= 98.85:
            value = int( ( value + 273.15 ) * 100 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def alarm_low_temp_clear( self ):
        reg_addr = b'\x03\x2B'
        response = self._read( 2, reg_addr, 'int' )
        if response == 0: return self.ERROR_VAL
        if response >= 17400 and response <= 37200: return response / 100 - 273.15
        else: return self.ERROR_VAL
    @alarm_low_temp_clear.setter
    def alarm_low_temp_clear( self, value ):
        reg_addr = b'\x03\x2B'
        if value >= -99.15 and value <= 98.85:
            value = int( ( value + 273.15 ) * 100 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def alarm_high_temp( self ):
        reg_addr = b'\x03\x2C'
        response = self._read( 2, reg_addr, 'int' )
        if response == 0: return self.ERROR_VAL
        if response >= 17400 and response <= 37200: return response / 100 - 273.15
        else: return self.ERROR_VAL
    @alarm_high_temp.setter
    def alarm_high_temp( self, value ):
        reg_addr = b'\x03\x2C'
        if value >= -99.15 and value <= 98.85:
            value = int( ( value + 273.15 ) * 100 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def alarm_high_temp_clear( self ):
        reg_addr = b'\x03\x2D'
        response = self._read( 2, reg_addr, 'int' )
        if response == 0: return self.ERROR_VAL
        if response >= 17400 and response <= 37200: return response / 100 - 273.15
        else: return self.ERROR_VAL
    @alarm_high_temp_clear.setter
    def alarm_high_temp_clear( self, value ):
        reg_addr = b'\x03\x2D'
        if value >= -99.15 and value <= 98.85:
            value = int( ( value + 273.15 ) * 100 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def alarm_mid_voltage( self ):
        reg_addr = b'\x03\x31'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 0 and response <= 990: return response / 10
        else: return self.ERROR_VAL
    @alarm_mid_voltage.setter
    def alarm_mid_voltage( self, value ):
        reg_addr = b'\x03\x31'
        if value >= 0 and value <= 99:
            value = int( value * 10 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def alarm_mid_voltage_clear( self ):
        reg_addr = b'\x03\x32'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 0 and response <= 990: return response / 10
        else: return self.ERROR_VAL
    @alarm_low_soc_clear.setter
    def alarm_low_soc_clear( self, value ):
        reg_addr = b'\x03\x32'
        if value >= 0 and value <= 99:
            value = int( value * 10 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def alarm_acknowledge( self ):
        reg_addr = b'\x03\x1F'
        response = self._read( 2, reg_addr, 'int_ovvr' )
        return "Acknowledged"
#------------------------------- End Alarm Settings ----------------------------

#-------------------------------- Relay Settings -------------------------------
    @property
    def relay_mode( self ):
        reg_addr = b'\x03\x4F'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == 0: return "DEFAULT"
            if response == 1: return "CHARGE"
            if response == 2: return "REM"
            return "UNKNOWN"
        if response == 0 or response == 1 or response == 2: return response
        else: return self.ERROR_VAL
    @relay_mode.setter
    def relay_mode( self, value ):
        reg_addr = b'\x03\x4F'
        if value == 0 or value == 1 or value == 2:
            value = int( value ).to_bytes( 1, byteorder='little', signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property 
    def relay_invert( self ):
        reg_addr = b'\x03\x4D'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == 0: return "OFF"
            if response == 1: return "ON"
            return "UNKNOWN"
        if response == 0 or response == 1: return response
        else: return self.ERROR_VAL
    @relay_invert.setter
    def relay_invert( self, value ):
        reg_addr = b'\x03\x4D'
        if value == 0 or value == 1:
            value = int( value ).to_bytes( 1, byteorder='little', signed=False )
            self._write( value, 1, reg_addr, 'int' )
    
    @property
    def relay_state( self ):
        reg_addr = b'\x03\x4E'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == 0: return "OPEN"
            if response == 1: return "CLOSED"
            return "UNKNOWN"
        if response == 0 or response == 1: return response  
        else: return self.ERROR_VAL
    @relay_state.setter
    def relay_state( self, value ):
        reg_addr = b'\x03\x4E'
        if value == 0 or value == 1:
            value = int( value ).to_bytes( 1, byteorder='little', signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property
    def relay_min_enable_time( self ):
        reg_addr = b'\x10\x0a'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 0 and response <= 500: return response 
        else: return self.ERROR_VAL
    @relay_min_enable_time.setter
    def relay_min_enable_time( self, value ):
        reg_addr = b'\x10\x0a'
        if value >= 0 and value <= 500: 
            value = int( value ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def relay_disable_time( self ):
        reg_addr = b'\x10\x0b'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 0 and response <= 500: return response 
        else: return self.ERROR_VAL
    @relay_disable_time.setter
    def relay_disable_time( self, value ):
        reg_addr = b'\x10\x0b'
        if value >= 0 and value <= 500: 
            value = int( value ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property 
    def relay_low_voltage( self ):
        reg_addr = b'\x03\x50'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 0 and response <= 950: return response / 10
        else: return self.ERROR_VAL
    @relay_low_voltage.setter
    def relady_low_voltage( self, value ):
        reg_addr = b'\x03\x50'
        if value >= 0 and value <= 95:
            value = int( value * 10 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property 
    def relay_low_voltage_clear( self ):
        reg_addr = b'\x03\x51'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 0 and response <= 950: return response / 10 
        else: return self.ERROR_VAL
    @relay_low_voltage_clear.setter
    def relay_low_voltage_clear( self, value ):
        reg_addr = b'\x03\x51'
        if value >= 0 and value <= 95:
            value = int( value * 10 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property 
    def relay_high_voltage( self ):
        reg_addr = b'\x03\x52'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 0 and response <= 950: return response / 10
        else: return self.ERROR_VAL
    @relay_high_voltage.setter
    def relady_high_voltage( self, value ):
        reg_addr = b'\x03\x52'
        if value >= 0 and value <= 95:
            value = int( value * 10 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property 
    def relay_high_voltage_clear( self ):
        reg_addr = b'\x03\x53'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 0 and response <= 950: return response / 10 
        else: return self.ERROR_VAL
    @relay_high_voltage_clear.setter
    def relay_high_voltage_clear( self, value ):
        reg_addr = b'\x03\x53'
        if value >= 0 and value <= 95:
            value = int( value * 10 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property 
    def relay_low_starter( self ):
        reg_addr = b'\x03\x54'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 0 and response <= 950: return response / 10
        else: return self.ERROR_VAL
    @relay_low_starter.setter
    def relady_low_starter( self, value ):
        reg_addr = b'\x03\x54'
        if value >= 0 and value <= 95:
            value = int( value * 10 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property 
    def relay_low_starter_clear( self ):
        reg_addr = b'\x03\x55'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 0 and response <= 950: return response / 10 
        else: return self.ERROR_VAL
    @relay_low_starter_clear.setter
    def relay_low_starter_clear( self, value ):
        reg_addr = b'\x03\x55'
        if value >= 0 and value <= 95:
            value = int( value * 10 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property 
    def relay_high_starter( self ):
        reg_addr = b'\x03\x56'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 0 and response <= 950: return response / 10
        else: return self.ERROR_VAL
    @relay_high_starter.setter
    def relady_high_starter( self, value ):
        reg_addr = b'\x03\x56'
        if value >= 0 and value <= 95:
            value = int( value * 10 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property 
    def relay_high_starter_clear( self ):
        reg_addr = b'\x03\x57'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 0 and response <= 950: return response / 10 
        else: return self.ERROR_VAL
    @relay_high_starter_clear.setter
    def relay_high_starter_clear( self, value ):
        reg_addr = b'\x03\x57'
        if value >= 0 and value <= 95:
            value = int( value * 10 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def relay_low_temp( self ):
        reg_addr = b'\x03\x5A'
        response = self._read( 2, reg_addr, 'int' )
        if response == 0: return self.ERROR_VAL
        if response >= 17400 and response <= 37200: return response / 100 - 273.15
        else: return self.ERROR_VAL
    @relay_low_temp.setter
    def relay_low_temp( self, value ):
        reg_addr = b'\x03\x5A'
        if value >= -99.15 and value <= 98.85:
            value = int( ( value + 273.15 ) * 100 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def relay_low_temp_clear( self ):
        reg_addr = b'\x03\x5B'
        response = self._read( 2, reg_addr, 'int' )
        if response == 0: return self.ERROR_VAL
        if response >= 17400 and response <= 37200: return response / 100 - 273.15
        else: return self.ERROR_VAL
    @relay_low_temp_clear.setter
    def relay_low_temp_clear( self, value ):
        reg_addr = b'\x03\x5B'
        if value >= -99.15 and value <= 98.85:
            value = int( ( value + 273.15 ) * 100 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def relay_high_temp( self ):
        reg_addr = b'\x03\x5C'
        response = self._read( 2, reg_addr, 'int' )
        if response == 0: return self.ERROR_VAL
        if response >= 17400 and response <= 37200: return response / 100 - 273.15
        else: return self.ERROR_VAL
    @relay_high_temp.setter
    def relay_high_temp( self, value ):
        reg_addr = b'\x03\x5C'
        if value >= -99.15 and value <= 98.85:
            value = int( ( value + 273.15 ) * 100 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def relay_high_temp_clear( self ):
        reg_addr = b'\x03\x5D'
        response = self._read( 2, reg_addr, 'int' )
        if response == 0: return self.ERROR_VAL
        if response >= 17400 and response <= 37200: return response / 100 - 273.15
        else: return self.ERROR_VAL
    @relay_high_temp_clear.setter
    def relay_high_temp_clear( self, value ):
        reg_addr = b'\x03\x5D'
        if value >= -99.15 and value <= 98.85:
            value = int( ( value + 273.15 ) * 100 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def relay_mid_voltage( self ):
        reg_addr = b'\x03\x61'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 0 and response <= 990: return response / 10
        else: return self.ERROR_VAL
    @relay_mid_voltage.setter
    def relay_mid_voltage( self, value ):
        reg_addr = b'\x03\x61'
        if value >= 0 and value <= 99:
            value = int( value * 10 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def relay_mid_voltage_clear( self ):
        reg_addr = b'\x03\x62'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 0 and response <= 990: return response / 10
        else: return self.ERROR_VAL
    @relay_low_soc_clear.setter
    def relay_low_soc_clear( self, value ):
        reg_addr = b'\x03\x62'
        if value >= 0 and value <= 99:
            value = int( value * 10 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )
#----------------------------- End Relay Settings ------------------------------

#------------------------------ Display Settings -------------------------------
    @property
    def backlight_intensity( self ):
        reg_addr = b'\xEE\xFE'
        response = self._read( 1, reg_addr, 'int' )
        if response >= 0 and response <= 9: return response 
        else: return self.ERROR_VAL
    @backlight_intensity.setter
    def backlight_intensity( self, value ):
        reg_addr = b'\xEE\xFE'
        if value >= 0 and value <= 9: 
            value = int( value ).to_bytes( 1, byteorder='little', signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property
    def backlight_always_on( self ):
        reg_addr = b'\x04\x00'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == 0: return "OFF"
            if response == 1: return "ON"
            return "UNKNOWN"
        if response == 0 or response == 1: return response 
        else: return self.ERROR_VAL
    @backlight_always_on.setter
    def backlight_always_on( self, value ):
        reg_addr = b'\x04\x00'
        if value == 0 or value == 1:
            value = int(value).to_bytes( 1, byteorder='little', signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property
    def scroll_speed( self ):
        reg_addr = b'\xEE\xF5'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == 1: return "SLOW" 
            if response == 2: return "MED-SLOW"
            if response == 3: return "MEDIUM"
            if response == 4: return "MED-FAST"
            if response == 5: return "FAST"
            return "UNKNOWN"
        if response >= 1 and response <= 5: return response 
        else: return self.ERROR_VAL
    @scroll_speed.setter
    def scroll_speed( self, value ):
        reg_addr = b'\xEE\xF5'
        response = self._read( 1, reg_addr, 'int' )
        if response >= 1 and response <= 5:
            value = int( value ).to_bytes( 1, byteorder='little', signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property
    def show_voltage( self ):
        reg_addr = b'\xEE\xE0'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == 0: return "OFF"
            if response == 1: return "ON"
            return "UNKNOWN"
        if response == 0 or response == 1: return response 
        else: return self.ERROR_VAL
    @show_voltage.setter
    def show_voltage( self, value ):
        reg_addr = b'\xEE\xE0'
        if value == 0 or value == 1:
            value = int( value ).to_bytes( 1, byteorder='little', signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property
    def show_aux_voltage( self ):
        reg_addr = b'\xEE\xE1'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == 0: return "OFF"
            if response == 1: return "ON"
            return "UNKNOWN"
        if response == 0 or response == 1: return response 
        else: return self.ERROR_VAL
    @show_aux_voltage.setter
    def show_aux_voltage( self, value ):
        reg_addr = b'\xEE\xE1'
        if value == 0 or value == 1:
            value = int( value ).to_bytes( 1, byteorder='little', signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property
    def show_mid_voltage( self ):
        reg_addr = b'\xEE\xE2'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == 0: return "OFF"
            if response == 1: return "ON"
            return "UNKNOWN"
        if response == 0 or response == 1: return response 
        else: return self.ERROR_VAL
    @show_mid_voltage.setter
    def show_mid_voltage( self, value ):
        reg_addr = b'\xEE\xE2'
        if value == 0 or value == 1:
            value = int( value ).to_bytes( 1, byteorder='little', signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property
    def show_current( self ):
        reg_addr = b'\xEE\xE3'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == 0: return "OFF"
            if response == 1: return "ON"
            return "UNKNOWN"
        if response == 0 or response == 1: return response 
        else: return self.ERROR_VAL
    @show_current.setter
    def show_current( self, value ):
        reg_addr = b'\xEE\xE3'
        if value == 0 or value == 1:
            value = int( value ).to_bytes( 1, byteorder='little', signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property
    def show_consumed_ah( self ):
        reg_addr = b'\xEE\xE4'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == 0: return "OFF"
            if response == 1: return "ON"
            return "UNKNOWN"
        if response == 0 or response == 1: return response 
        else: return self.ERROR_VAL
    @show_consumed_ah.setter
    def show_consumed_ah( self, value ):
        reg_addr = b'\xEE\xE4'
        if value == 0 or value == 1:
            value = int( value ).to_bytes( 1, byteorder='little', signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property
    def show_soc( self ):
        reg_addr = b'\xEE\xE5'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == 0: return "OFF"
            if response == 1: return "ON"
            return "UNKNOWN"
        if response == 0 or response == 1: return response 
        else: return self.ERROR_VAL
    @show_soc.setter
    def show_soc( self, value ):
        reg_addr = b'\xEE\xE5'
        if value == 0 or value == 1:
            value = int( value ).to_bytes( 1, byteorder='little', signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property
    def show_ttg( self ):
        reg_addr = b'\xEE\xE6'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == 0: return "OFF"
            if response == 1: return "ON"
            return "UNKNOWN"
        if response == 0 or response == 1: return response 
        else: return self.ERROR_VAL
    @show_ttg.setter
    def show_ttg( self, value ):
        reg_addr = b'\xEE\xE6'
        if value == 0 or value == 1:
            value = int( value ).to_bytes( 1, byteorder='little', signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property
    def show_temperature( self ):
        reg_addr = b'\xEE\xE7'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == 0: return "OFF"
            if response == 1: return "ON"
            return "UNKNOWN"
        if response == 0 or response == 1: return response 
        else: return self.ERROR_VAL
    @show_temperature.setter
    def show_temperature( self, value ):
        reg_addr = b'\xEE\xE7'
        if value == 0 or value == 1:
            value = int( value ).to_bytes( 1, byteorder='little', signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property
    def show_power( self ):
        reg_addr = b'\xEE\xE8'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == 0: return "OFF"
            if response == 1: return "ON"
            return "UNKNOWN"
        if response == 0 or response == 1: return response 
        else: return self.ERROR_VAL
    @show_power.setter
    def show_power( self, value ):
        reg_addr = b'\xEE\xE8'
        if value == 0 or value == 1:
            value = int( value ).to_bytes( 1, byteorder='little', signed=False )
            self._write( value, 1, reg_addr, 'int' )
#----------------------------- End Display Settings ----------------------------

#------------------------------- Miscellaneous ---------------------------------
    @property
    def sw_version( self ):
        reg_addr = b'\xEE\xF9'
        response = self._read( 2, reg_addr, 'b' )
        hi_byte = int.from_bytes( response[:-1], signed=False )
        lo_byte = int.from_bytes( response[-1:], signed=False )
        if lo_byte < 10: return ( str( hi_byte ) + ".0" + str( lo_byte ) )
        else: return str( hi_byte ) + "." + str( lo_byte ) 
    
    @property
    def setup_lock( self ):
        reg_addr = b'\xEE\xF6'
        response = self._read( 1, reg_addr, 'int' )
        if response == 0 or response == 1: return response 
        else: return self.ERROR_VAL
    @setup_lock.setter
    def setup_lock( self, value ):
        reg_addr = b'\xEE\xF6'
        if value == 0 or value == 1: 
            value = int( value ).to_bytes( 1, byteorder='little', signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property
    def shunt_amps( self ):
        reg_addr = b'\xEE\xFB'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 1 and response <= 9999: return response 
        else: return self.ERROR_VAL 
    @shunt_amps.setter
    def shunt_amps( self, value ):
        reg_addr = b'\xEE\xFB'
        if value >= 1 and value <= 9999:
            value = int( value ).to_bytes( 2, byteorder='little', signed=False)
            self._write( value, 2, reg_addr, 'int' )

    @property
    def shunt_volts( self ):
        reg_addr = b'\xEE\xFA'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 1 and response <= 100: return response / 1000
        else: return self.ERROR_VAL 
    @shunt_volts.setter
    def shunt_volts( self, value ):
        reg_addr = b'\xEE\xFA'
        if value >= 0.001 and value <= 0.1:
            value = int( value * 1000 ).to_bytes( 2, byteorder='little', signed=False)
            self._write( value, 2, reg_addr, 'int' )
    
    @property
    def temperature_unit( self ):
        reg_addr = b'\xEE\xF7'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == 0: return "CELSIUS"
            if response == 1: return "FARENHEIT"
            return "UNKNOWN"
        if response == 0 or response == 1: return response 
        else: return self.ERROR_VAL
    @temperature_unit.setter
    def temperature_unit( self, value ):
        reg_addr = b'\xEE\xF7'
        if value == 0 or value == 1:
            value = int(value).to_bytes( 1, byteorder='little', signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property
    def temperature_coeff( self ):
        reg_addr = b'\xEE\xF4'
        response = self._read( 2, reg_addr, 'int' )
        if response >= 0 and response <= 200: return response / 10
        else: return self.ERROR_VAL
    @temperature_coeff.setter
    def temperature_coeff( self, value ):
        reg_addr = b'\xEE\xF4'
        if value >= 0 and value <= 20:
            value = int( value * 10 ).to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def aux_input( self ):
        reg_addr = b'\xEE\xF8'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == 0: return "STARTER"
            if response == 1: return "MID-POINT VOLTAGE"
            if response == 2: return "TEMPERATURE"
            return "UNKNOWN"
        if response == 0 or response == 1 or response == 2: return response 
        else: return self.ERROR_VAL
    @aux_input.setter
    def aux_input( self, value ):
        reg_addr = b'\xEE\xF8'
        if value >= 0 and value <= 2: 
            value = int( value ).to_bytes( 1, byteorder='little', signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property
    def start_synchronized( self ):
        reg_addr = b'\x0F\xFD'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == 0: return "OFF"
            if response == 1: return "ON"
            return "UNKNOWN"
        if response == 0 or response == 1: return response 
        else: return self.ERROR_VAL
    @start_synchronized.setter
    def start_synchronized( self, value ):
        reg_addr = b'\x0F\xFD'
        if value == 0 or value == 1:
            value = int(value).to_bytes( 1, byteorder='little', signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property
    def settings_changed_timestamp( self ):
        reg_addr = b'\xEC\x41'
        response = self._read( 4, reg_addr, 'b' )
        try:
            if response == b'\xFF\xFF\xFF\xFF': return self.ERROR_VAL
            else: return int.from_bytes( response, byteorder='little', signed=False )
        except: return self.ERROR_VAL

    @property
    def bluetooth_mode( self ):
        reg_addr = b'\x00\x90'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE: 
            if response == 0: return "OFF"
            if response == 1: return "ON"
            return "UNKNOWN"
        if response == 0 or response == 1: return response 
        else: return self.ERROR_VAL
    @bluetooth_mode.setter
    def bluetooth_mode( self, value ):
        reg_addr = b'\x00\x90'
        if value == 0 or value == 1:
            value = int(value).to_bytes( 1, byteorder='little', signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property
    def dc_monitor_mode( self ):
        reg_addr = b'\xEE\xB8'
        response = self._read( 2, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == -9: return "SOLAR CHARGER"
            if response == -8: return "WIND TURBINE"
            if response == -7: return "SHAFT GENERATOR"
            if response == -6: return "ALTERNATOR"
            if response == -5: return "FUEL CELL"
            if response == -4: return "WATER GENERATOR"
            if response == -3: return "DC-DC CHARGER"
            if response == -2: return "AC CHARGER"
            if response == -1: return "GENERIC SOURCE"
            if response == 0: return "BATTERY MONITOR"
            if response == 1: return "GENERIC LOAD"
            if response == 2: return "ELECTRIC DRIVE"
            if response == 3: return "FRIDGE"
            if response == 4: return "WATER PUMP"
            if response == 5: return "BILGE PUMP"
            if response == 6: return "DC SYSTEM"
            if response == 7: return "INVERTER"
            if response == 8: return "WATER HEATER"
            return "UNKNONW"
        if response >= -9 and response <= 8: return response
        else: return self.ERROR_VAL
#----------------------------- End miscellaneous -------------------------------
#============================== END PROPERTIRES ================================

#============================== Basic Functions ================================
#-------------------------------- zero_current ---------------------------------
    def zero_current( self ):
        reg_addr = b'\x10\x29'
        self._write( b'\x01', 1, reg_addr, 'int' )
#-------------------------------------------------------------------------------
#-------------------------------- synchronize ----------------------------------
    def synchronize( self ):
        reg_addr = b'\x10\x2c'
        self._write( b'\x01', 1, reg_addr, 'int' )
#-------------------------------------------------------------------------------
#------------------------------ restore_defaults -------------------------------
    def restore_defaults( self ):
        reg_addr = b'\x00\x04'
        self._write( b'\x01', 1, reg_addr, 'int' )
#-------------------------------------------------------------------------------
#------------------------------- clear_history ---------------------------------
    def clear_history( self ):
        reg_addr = b'\x10\x30'
        self._write( b'\x01', 1, reg_addr, 'int' )
#-------------------------------------------------------------------------------
#----------------------------------- ping --------------------------------------
    def ping( self ):
        response = self._send_cmd( "1" )
        if response == self.ERROR_VAL: return response 
        else: return ( response - 16384 ) / 100 
#-------------------------------------------------------------------------------
#---------------------------------- restart ------------------------------------
    def restart( self ):
        response = self._send_cmd( "6" )
        if response == "RESTART": 
            print( self._PREFIX + "Succesfully issued restart command." )
            time.sleep( 3 )
        else: print( self._PREFIX + "Failed to send the restart command.")
#-------------------------------------------------------------------------------
#--------------------------- application_version -------------------------------
    def application_version( self ):
        response = self._send_cmd( "3" )
        if response == self.ERROR_VAL: return response 
        else: return ( response - 16384 ) / 100 
#-------------------------------------------------------------------------------
#=========================== END BASIC FUNCTIONS ===============================

# Tester Function for direct call
if __name__ == '__main__':
    bmv = bmvhex( 'COM8' )
    #bmv.DEBUG = True
    #bmv.DESCRIPTIVE = False
    #bmv.readall

    # 0x01** product information registers
    #print( bmv.PREFIX + "VE.Direct device product id = " + str( bmv.pid ) )
    #print( bmv.PREFIX + "VE.Direct device product revision = " + str( bmv.product_revision ) )
    #print( bmv.PREFIX + "VE.Direct device serial number = " + str( bmv.serial_number ) )
    #print( bmv.PREFIX + "VE.Direct device model name = " + str( bmv.model_name ) )
    print( bmv.PREFIX + "VE.Direct device description = " + str( bmv.description ) )
    #print( bmv.PREFIX + "VE.Direct device uptime = " + str( bmv.device_uptime ) + " [s]." )
    #print( bmv.PREFIX + "VE.Direct bluetooth capabilities = " + str( bmv.bluetooth_capabilities ) )

    # Monitor Related Registers
    #print( bmv.PREFIX + "BMV main voltage = " + str( bmv.main_voltage ) + " [V]." )
    #print( bmv.PREFIX + "BMV aux voltage = " + str( bmv.aux_voltage ) + " [V]." )
    #print( bmv.PREFIX + "BMV two byte current = " + str( bmv.current_twobyte ) + " [A]." )
    #print( bmv.PREFIX + "BMV four byte current = " + str( bmv.current_fourbyte ) + " [A]." )
    #print( bmv.PREFIX + "BMV power = " + str( bmv.power ) + " [W]." )
    #print( bmv.PREFIX + "BMV consumed amphours = " + str( bmv.consumed_ah ) + " [AHr]." )
    #print( bmv.PREFIX + "BMV state of charge = " + str( bmv.soc ) + " [%]." )
    #print( bmv.PREFIX + "BMV TTG (idk what that stands for) = " + str( bmv.ttg ) + " [min]." )
    #print( bmv.PREFIX + "BMV temperature = " + str( bmv.temperature ) + " [°C]." )
    #print( bmv.PREFIX + "BMV mid-point voltage = " + str( bmv.mid_voltage ) + " [V]." )
    #print( bmv.PREFIX + "BMV mid-point deviation = " + str( bmv.mid_deviation ) + " [%]." )
    #print( bmv.PREFIX + "BMV synchronization state = " + str( bmv.synch_state ) )

    # Historical Data Registers
    #print( bmv.PREFIX + "BMV depth of deepest discharge = " + str( bmv.deepest_discharge ) + " [AHr]." )
    #print( bmv.PREFIX + "BMV depth of last discharge = " + str( bmv.last_discharge_depth ) + " [AHr]." )
    #print( bmv.PREFIX + "BMV average depth of discharge = " + str( bmv.avg_discharge_depth ) + " [AHr]." )
    #print( bmv.PREFIX + "BMV number of cycles = " + str( bmv.cycles ) + " [Count]." )
    #print( bmv.PREFIX + "BMV number of full discharges = " + str( bmv.full_discharges ) + " [Count]." )
    #print( bmv.PREFIX + "BMV cumulative amphours = " + str( bmv.cumulative_amphours ) + " [AHr]." )
    #print( bmv.PREFIX + "BMV minimum voltage = " + str( bmv.min_voltage ) + " [V]." )
    #print( bmv.PREFIX + "BMV maximum voltage = " + str( bmv.max_voltage ) + " [V]." )
    #print( bmv.PREFIX + "BMV time since last full = " + str( bmv.since_charge ) + " [s]." )
    #print( bmv.PREFIX + "BMV number of automatic synchronizations = " + str( bmv.auto_syncs ) + " [Count]." )
    #print( bmv.PREFIX + "BMV number of low voltage alarms = " + str( bmv.low_alarms ) + " [Count]." )
    #print( bmv.PREFIX + "BMV number of high voltage alarms = " + str( bmv.high_alarms ) + " [Count]." )
    #print( bmv.PREFIX + "BMV minimum aux voltage = " + str( bmv.min_aux_voltage ) + " [V]." )
    #print( bmv.PREFIX + "BMV maximum aux voltage = " + str( bmv.max_aux_voltage ) + " [V]." )
    #print( bmv.PREFIX + "BMV total energy discharged (produced energy) = " + str( bmv.discharged_energy ) + " [kWh]." )
    #print( bmv.PREFIX + "BMV total energy charged (consumed energy) = " + str( bmv.charged_energy ) + " [kWh]." )

    # Monitor Settings Registers
    #print( bmv.PREFIX + "BMV battery capacity = " + str( bmv.battery_capacity ) + " [AHr]." )
    #print( bmv.PREFIX + "BMV charged voltage = " + str( bmv.charged_voltage ) + " [V]." )
    #print( bmv.PREFIX + "BMV tail current = " + str( bmv.tail_current ) + " [%]." )
    #print( bmv.PREFIX + "BMV charged detection time = " + str( bmv.charged_detection_time ) + " [min]." )
    #print( bmv.PREFIX + "BMV charge efficiency = " + str( bmv.charge_efficiency ) + " [%]." )
    #print( bmv.PREFIX + "BMV peukert coefficient = " + str( bmv.peukert_coeff ) + " []." )
    #print( bmv.PREFIX + "BMV current threshold = " + str( bmv.current_threshold ) + " [A]." )
    #print( bmv.PREFIX + "BMV TTG delta T = " + str( bmv.ttg_delta_t ) + " [min]." )
    #print( bmv.PREFIX + "BMV discharge floor (Relay low soc set) = " + str( bmv.discharge_floor ) + " [%]." )
    #print( bmv.PREFIX + "BMV relay low soc clear = " + str( bmv.relay_low_soc_clear ) + " [%]." )
    #print( bmv.PREFIX + "BMV user current zero = " + str( bmv.user_current_zero ) + " [ADC Count]." )

    # Alarm Settings
    #print( bmv.PREFIX + "BMV alarm buzzer = " + str( bmv.alarm_buzzer ) + " [Code]." )
    #print( bmv.PREFIX + "BMV alarm low main voltage = " + str( bmv.alarm_low_voltage ) + " [V]." )
    #print( bmv.PREFIX + "BMV alarm low main voltage clear = " + str( bmv.alarm_low_voltage_clear ) + " [V]." )
    #print( bmv.PREFIX + "BMV alarm high main voltage = " + str( bmv.alarm_high_voltage ) + " [V]." )
    #print( bmv.PREFIX + "BMV alarm high main voltage clear = " + str( bmv.alarm_high_voltage_clear ) + " [V]." )
    #print( bmv.PREFIX + "BMV alarm low starter voltage = " + str( bmv.alarm_low_starter ) + " [V]." )
    #print( bmv.PREFIX + "BMV alarm low starter voltage clear = " + str( bmv.alarm_low_starter_clear ) + " [V]." )
    #print( bmv.PREFIX + "BMV alarm high starter voltage = " + str( bmv.alarm_high_starter ) + " [V]." )
    #print( bmv.PREFIX + "BMV alarm high starter voltage clear = " + str( bmv.alarm_high_starter_clear ) + " [V]." )
    #print( bmv.PREFIX + "BMV alarm low state of charge = " + str( bmv.alarm_low_soc ) + " [%]." )
    #print( bmv.PREFIX + "BMV alarm low state of charge clear = " + str( bmv.alarm_low_soc_clear ) + " [%]." )
    #print( bmv.PREFIX + "BMV alarm low temperature = " + str( bmv.alarm_low_temp ) + " [°C]." )
    #print( bmv.PREFIX + "BMV alarm low temperature clear = " + str( bmv.alarm_low_temp_clear ) + " [°C]." )
    #print( bmv.PREFIX + "BMV alarm high temperature = " + str( bmv.alarm_high_temp ) + " [°C]." )
    #print( bmv.PREFIX + "BMV alarm high temperature clear = " + str( bmv.alarm_high_temp_clear ) + " [°C]." )
    #print( bmv.PREFIX + "BMV alarm mid voltage = " + str( bmv.alarm_mid_voltage ) + " [V]." )
    #print( bmv.PREFIX + "BMV alarm mid voltage clear = " + str( bmv.alarm_mid_voltage_clear ) + " [V]." )
    #print( bmv.PREFIX + "BMV alarm acknowledge = " + str( bmv.alarm_acknowledge ) + " [].")

    # Relay Settings 
    #print( bmv.PREFIX + "BMV relay mode = " + str( bmv.relay_mode ) + " [Code]." )
    #print( bmv.PREFIX + "BMV relay invert = " + str( bmv.relay_invert ) + " [Code]." )
    #print( bmv.PREFIX + "BMV relay state = " + str( bmv.relay_state ) + " [Code]." )
    #print( bmv.PREFIX + "BMV relay minimal enabled time = " + str( bmv.relay_min_enable_time ) + " [min]." )
    #print( bmv.PREFIX + "BMV relay disable time = " + str( bmv.relay_disable_time ) + " [min]." )
    #print( bmv.PREFIX + "BMV relay low main voltage = " + str( bmv.relay_low_voltage ) + " [V]." )
    #print( bmv.PREFIX + "BMV relay low main voltage clear = " + str( bmv.relay_low_voltage_clear ) + " [V]." )
    #print( bmv.PREFIX + "BMV relay high main voltage = " + str( bmv.relay_high_voltage ) + " [V]." )
    #print( bmv.PREFIX + "BMV relay high main voltage clear = " + str( bmv.relay_high_voltage_clear ) + " [V]." )
    #print( bmv.PREFIX + "BMV relay low starter voltage = " + str( bmv.relay_low_starter ) + " [V]." )
    #print( bmv.PREFIX + "BMV relay low starter voltage clear = " + str( bmv.relay_low_starter_clear ) + " [V]." )
    #print( bmv.PREFIX + "BMV relay high starter voltage = " + str( bmv.relay_high_starter ) + " [V]." )
    #print( bmv.PREFIX + "BMV relay high starter voltage clear = " + str( bmv.relay_high_starter_clear ) + " [V]." )
    #print( bmv.PREFIX + "BMV relay low temperature = " + str( bmv.relay_low_temp ) + " [°C]." )
    #print( bmv.PREFIX + "BMV relay low temperature clear = " + str( bmv.relay_low_temp_clear ) + " [°C]." )
    #print( bmv.PREFIX + "BMV relay high temperature = " + str( bmv.relay_high_temp ) + " [°C]." )
    #print( bmv.PREFIX + "BMV relay high temperature clear = " + str( bmv.relay_high_temp_clear ) + " [°C]." )
    #print( bmv.PREFIX + "BMV relay mid voltage = " + str( bmv.relay_mid_voltage ) + " [V]." )
    #print( bmv.PREFIX + "BMV relay mid voltage clear = " + str( bmv.relay_mid_voltage_clear ) + " [V]." )

    # Display Settings
    #print( bmv.PREFIX + "BMV backlight intensity = " + str( bmv.backlight_intensity ) + " [Code]." )
    #print( bmv.PREFIX + "BMV backlight always on = " + str( bmv.backlight_always_on ) + " [Code]." )
    #print( bmv.PREFIX + "BMV scroll speed = " + str( bmv.scroll_speed ) + " [Code]." )
    #print( bmv.PREFIX + "BMV show voltage = " + str( bmv.show_voltage ) + " [Code]." )
    #print( bmv.PREFIX + "BMV show auxilliary voltage = " + str( bmv.show_aux_voltage ) + " [Code]." )
    #print( bmv.PREFIX + "BMV show mid voltage = " + str( bmv.show_mid_voltage ) + " [Code]." )
    #print( bmv.PREFIX + "BMV show current = " + str( bmv.show_current ) + " [Code]." )
    #print( bmv.PREFIX + "BMV show consumed AHr = " + str( bmv.show_consumed_ah ) + " [Code]." )
    #print( bmv.PREFIX + "BMV show SOC = " + str( bmv.show_soc ) + " [Code]." )
    #print( bmv.PREFIX + "BMV show TTG = " + str( bmv.show_ttg ) + " [Code]." )
    #print( bmv.PREFIX + "BMV show temperature = " + str( bmv.show_temperature ) + " [Code]." )
    #print( bmv.PREFIX + "BMV show power = " + str( bmv.show_power ) + " [Code]." )

    # Miscellaneous
    #print( bmv.PREFIX + "BMV software version = " + str( bmv.sw_version ) + " [Maj.Min]." )
    #print( bmv.PREFIX + "BMV setup lock = " + str( bmv.setup_lock ) + " [Code]." )
    #print( bmv.PREFIX + "BMV shunt amps = " + str( bmv.shunt_amps ) + " [A]." )
    #print( bmv.PREFIX + "BMV shunt volts = " + str( bmv.shunt_volts ) + " [V]." )
    #print( bmv.PREFIX + "BMV temperature unit = " + str( bmv.temperature_unit ) + " [Code]." )
    #print( bmv.PREFIX + "BMV temperature coefficient = " + str( bmv.temperature_coeff ) + " [%CAP/°C]." )
    #print( bmv.PREFIX + "BMV auxilliary input type = " + str( bmv.aux_input ) + " [Code]." )
    #print( bmv.PREFIX + "BMV start synchronized setting = " + str( bmv.start_synchronized ) + " [Code]." )
    #print( bmv.PREFIX + "BMV settings changed timestamp = " + str( bmv.settings_changed_timestamp ) + " [s from 1/1/1970]." )
    #print( bmv.PREFIX + "BMV bluetooth mode = " + str( bmv.bluetooth_mode ) + " [Code]." )
    #print( bmv.PREFIX + "BMV DC monitor mode = " + str( bmv.dc_monitor_mode ) + " [Code]." )

    # Basic Commands
    #bmv.readall
    #bmv.zero_current()
    #bmv.synchronize()
    #bmv.restore_defaults()
    #bmv.restart() 
    #print( bmv.PREFIX + "Ping response = " + str( bmv.ping() ) + ", which is the application version." )
    #print( bmv.PREFIX + "Application version = " + str( bmv.application_version() ) + "." )
    #bmv.clear_history()
