#!/usr/bin/env python3
#******************************** Dependencies *********************************
import serial
import time
#*******************************************************************************
#==================================== Intro ====================================
    # Aaron Kehl
    # USACE - ERDC - CRREL
    # Summer 2024
    #
    # VE.Direct Hex Solar Protocol class for victron solar charge controllers.
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

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< VEDirect Class >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#******************************** initialize ***********************************
class vedirect(object):
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
    def DEBUG( self, value ): self._DESCRIPTIVE = value     
    
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
#===============================================================================

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
        tx_msg = ( ":" + cmd ).encode( "utf-8" )
        crc = self._crc_calc( self._ascii_bytes_to_bytes( cmd.encode( "utf-8" ) ) )
        tx_crc = self._bytes_to_ascii_bytes( crc )
        tx_nln = str.encode( "\n", 'utf-8' )
        tx_msg = tx_msg + tx_crc + tx_nln
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
                        rx_msg.find( b'\t' ) == -1:
                        # we have a good return that is not the asynch message
                        break
                    else:
                        # sometimes we fail due to the heartbeat
                        # coming from the ve.device, this delay lets
                        # it finish before we try to poll the device again
                        serial_device.write( b'\x13\x10' )
                        rx_msg = serial_device.read()
                        time.sleep( 0.2 )
                        serial_device.reset_input_buffer()
                        time.sleep( 0.1 ) 
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
                rx_cmd = rx_msg[:2]
                rx_dat = rx_msg[2:6]
                rx_crc = rx_msg[6:8]
                rx_nln = rx_msg[8:]
                
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
                    print( self._PREFIX + "End of command line character not detected! rx_nln = " + str( rx_nln ) + ", tx_nln" + str( tx_nln ) )
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
                        rx_msg.find( b'\t' ) == -1:
                        # we have a good return that is not the asynch message
                        break
                    else:
                        # sometimes we fail due to the heartbeat
                        # coming from the ve.device, this delay lets
                        # it finish before we try to poll the device again
                        serial_device.write( b'\x13\x10' )
                        rx_msg = serial_device.read()
                        time.sleep( 0.2 )
                        serial_device.reset_input_buffer()
                        time.sleep( 0.1 ) 

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
            rx_cmd = rx_msg[:2]
            rx_reg = rx_msg[2:6]
            rx_flg = rx_msg[6:8]
            rx_dat = rx_msg[8:-3]
            rx_crc = rx_msg[-3:-1]
            rx_nln = rx_msg[-1:]
            
            # update data and crc to bytes from ascii bytes
            rx_dat = self._ascii_bytes_to_bytes( rx_dat )
            if format == 'int': rx_dat = self._flip( rx_dat )
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
            print( self._PREFIX + "End of command line character not detected! rx_nln = " + str( rx_nln ) + ", nln" + str( tx_nln ) )
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
                        rx_msg.find( b'\t' ) == -1:
                        break
                    else:
                        # sometimes we fail due to the heartbeat
                        # coming from the ve.device, this delay lets
                        # it finish before we try to poll the device again
                        serial_device.write( b'\x13\x10' )
                        rx_msg = serial_device.read()
                        time.sleep( 0.2 )
                        serial_device.reset_input_buffer()
                        time.sleep( 0.1 ) 

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
            print( self._PREFIX + "End of command line character not detected! rx_nln = " + str( rx_nln ) + ", nln" + str( tx_nln ) )
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
        while listening: 
            try: 
                bytestream = serial_device.read() 
                receive_message = receive_message + bytestream

                if bytestream == b'\xea':
                    print( self._PREFIX + "End of heartbeat detected..." )
                    #self._process_message( receive_message )
                    break

            except KeyboardInterrupt: 
                print( self._PREFIX + "Exiting listen..." )
                break

        print( self._PREFIX + "" + str( receive_message ) )
        print( "[VE_DIR] R(" + str( len( receive_message ) ) + " Bytes): " + self._to_hex( receive_message ) )
        
        self._close_port( serial_device )
        return "Fin" 
#-------------------------------------------------------------------------------
#===============================================================================

#================================ Properties ===================================
#----------------------------- Product Information -----------------------------
    @property 
    def firmware( self ):
        pass

    @property 
    def pid( self ):
        reg_addr = b'\x01\x00'
        response = self._read( 4, reg_addr, 'b' )
        if response[-1:] == b'\xFF':
            return self._to_hex( self._flip( response[1:-1] ) )
        else:
            return self._to_hex( self._flip( response ) )
    
    @property
    def group_id( self ):
        reg_addr = b'\x01\x04'
        return self._read( 1, reg_addr, 'b' )
    
    @property
    def serial_number( self ):
        reg_addr = b'\x01\x0A'
        return self._read( 64, reg_addr, 'str' )
    
    @property
    def model_name( self ):
        reg_addr = b'\x01\x0B'
        return self._read( 64, reg_addr, 'b' ).decode( 'utf-8' )
    
    @property
    def capabilities( self ):
        reg_addr = b'\x01\x40'
        cap_dict = {}
        cap_name = [ "Load Output Present", "Rotary Encoder Presesnt", "History Support", "Batterysafe Mode", 
                      "Adaptive Mode", "Manual Equalise", "Automatic Equalise", "Storage Mode", 
                      "Remote On/Off via Rx Pin", "Solar Timer/Streetlighting", "Alternative VE.Direct Tx Pn Function", 
                      "User Defined Load Switch", "Load Current in TEXT Protocol", "Panel Current", "BMS Support", 
                      "External Control Support", "Synchronized Charging Support", "Alarm Relay", 
                      "Alternative VE.Direct Rx Pin Function", "Virtual Load Output", "Virtual Relay", 
                      "Plugin Display Support", "22", "23", "24", "Load Automatic Energy Selector", "Battery Test", 
                      "PAYGO Support", "28", "29", "30", "31" ]
        
        cap_flag = self._bit_array( self._read( 4, reg_addr, 'int' ), 32 )
        
        len_flags = len( cap_flag ) - 1
        for i in range( len( cap_name ) ):
            cap_dict[ cap_name[i] ] = cap_flag[ len_flags - i ][-1:]
        
        return cap_dict
#-------------------------------------------------------------------------------

#---------------------------- Generic Device Control ---------------------------
    @property 
    def device_mode( self ):
        reg_addr = b'\x02\x00'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == 0 or response == 4: return "OFF"
            if response == 1: return "ON"
            return self.ERROR_VAL
        else:
            if response == 0 or response == 4: return 0
            if response == 1: return 1
            return self.ERROR_VAL
    
    @property
    def device_state( self ):
        reg_addr = b'\x02\x01'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response ==  0: return "NOT_CHARGING"
            if response ==  2: return "FAULT"
            if response ==  3: return "BULK"
            if response ==  4: return "ABSORPTION"
            if response ==  5: return "FLOAT"
            if response ==  6: return "STORAGE"
            if response ==  7: return "MANUAL EQUALISE"
            if response ==-11: return "WAKE-UP"
            if response == -9: return "AUTO EQUALISE"
            if response == -6: return "BLOCKED"
            if response == -4: return "EXTERNAL CONTROL"
            if response == -1: return "UNAVAILABLE"
            return "UNKNOWN DEVICE STATE"
        else: return response  
    
    @property
    def remote_control( self ):
        reg_addr = b'\x02\x02'
        response = self._bit_array( self._read( 4, reg_addr, 'int' ), 32 )
        return_value = response[len(response)-1][-1:]
        if self.DESCRIPTIVE:
            if return_value == 0: return "OFF"
            if return_value == 1: return "ON"
        return return_value 
    @remote_control.setter
    def remote_control( self, value ):
        reg_addr = b'\x02\x02'
        try:
            if value == "OFF": value = 0
            if value == "ON" : value = 1
        except: pass
        if value == 0 or value == 1: 
            value = value.to_bytes( 1, signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property
    def device_off_reason( self ):
        device_type = self.model_name
        if device_type.find( "MPPT RS" ) != -1:# or device_type.find( "BlueSolar" ) != -1:
            reg_addr = b'\x02\x07'
            return_value = self._bit_array( self._read( 4, reg_addr, 'int' ), 32 )
        elif device_type.find( "SmartSolar" ) != -1 :
            reg_addr = b'\x02\x05'
            return_value = self._bit_array( self._read( 1, reg_addr, 'int' ), 8 )
        else:
            print( self._PREFIX + "Model does not support this command." )
            return self.ERROR_VAL
        
        if self.DESCRIPTIVE and len( return_value ) > 1 :
            dict_off = {}
            dict_name = [ "No Input Power", "Physical Power Switch", "Soft Power Switch", \
                          "Remote Input", "Internal Reason", "Pay As You Go Out of Credit", \
                          "BMS Shutdown", "7", "8", "Battery Temp. too Low" \
                        ]
            dict_flag = return_value 

            len_flags = len( dict_flag ) - 1
            for i in range( len ( dict_name ) ):
                dict_off[ dict_name[i] ] = dict_flag[ len_flags - i ][-1:]

            return dict_off
        else:
            return return_value  
#-------------------------------------------------------------------------------

#------------------------------- Battery Settings ------------------------------
    @property
    def batterysafe_mode( self ):
        reg_addr = b'\xED\xFF'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == 0: return "OFF"
            if response == 1: return "ON"
            return self.ERROR_VAL
        else: return response 
    @batterysafe_mode.setter
    def batterysafe_mode( self, value ):
        reg_addr = b'\xED\xFF'
        try:
            if value == "OFF": value = 0
            if value == "ON" : value = 1
        except: pass
        if value == 0 or value == 1: 
            value = value.to_bytes( 1, signed=False )
            self._write( value, 1, reg_addr, 'int' )
        else:
            print( self._PREFIX + "Invalid input value " + str( value ) )

    @property
    def adaptive_mode( self ):
        reg_addr = b'\xED\xFE'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == 0: return "OFF"
            if response == 1: return "ON"
            return self.ERROR_VAL
        else: return response 
    @adaptive_mode.setter
    def adaptive_mode( self, value ):
        reg_addr = b'\xED\xFE'
        try:
            if value == "OFF": value = 0
            if value == "ON" : value = 1
        except: pass
        if value == 0 or value == 1: 
            value = value.to_bytes( 1, signed=False )
            self._write( value, 1, reg_addr, 'int' )
        else:
            print( self._PREFIX + "Invalid input value " + str( value ) )

    @property
    def automatic_equalisation_mode( self ):
        reg_addr = b'\xED\xFD'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response < 0 and response != self.ERROR_VAL:
                response = response * -1
            if response == 0:
                return_value = "OFF"
            elif response == 1:
                return_value = "EVERY DAY"
            elif response == 2:
                return_value = "EVERY OTHER DAY"
            elif response > 2 and response < 250:
                return_value = "EVERY " + str( response ) + " days."
            else:
                return_value = self.ERROR_VAL
        else:
            return_value = response 
        return return_value 
    @automatic_equalisation_mode.setter
    def automatic_equalisation_mode( self, value ):
        reg_addr = b'\xED\xFD'
        if value >= 0 and value < 250: 
            value = value.to_bytes( 1, signed=False )
            self._write( value, 1, reg_addr, 'int' )
        else:
            print( self._PREFIX + "Invalid input value " + str( value ) )

    @property
    def battery_bulk_time_limit( self ):
        reg_addr = b'\xED\xFC'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response
        return response / 100
    @battery_bulk_time_limit.setter
    def battery_bulk_time_limit( self, value ):
        reg_addr = b'\xED\xFC'
        value = int( value * 100 )
        if value >= 0 and value <= 10000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
            response = self._write( value, 2, reg_addr, 'int' )
        else:
            print( self._PREFIX + "Invalid input value " + str( value ) )

    @property
    def battery_absorption_time_limit( self ):
        reg_addr = b'\xED\xFB'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response
        return response / 100
    @battery_absorption_time_limit.setter
    def battery_absorption_time_limit( self, value ):
        reg_addr = b'\xED\xFB'
        value = int( value * 100 )
        if value >= 0 and value <= 10000: 
            value = value.to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def battery_absorption_voltage( self ):
        reg_addr = b'\xED\xF7'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response
        return response / 100
    @battery_absorption_voltage.setter 
    def battery_absorption_voltage( self, value ):
        reg_addr = b'\xED\xFB'
        value = int( value * 100 )
        if value >= 0 and value <= 10000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def battery_float_voltage( self ):
        reg_addr = b'\xED\xF6'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response
        return response / 100
    @battery_float_voltage.setter
    def battery_float_voltage( self, value ):
        reg_addr = b'\xED\xF6'
        value = int( value * 100 )
        if value >= 0 and value <= 10000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )
    
    @property
    def battery_equalisation_voltage( self ):
        reg_addr = b'\xED\xF4'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response
        return response / 100
    @battery_equalisation_voltage.setter
    def battery_equalisation_voltage( self, value ):
        reg_addr = b'\xED\xF4'
        value = int( value * 100 )
        if value >= 0 and value <= 10000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )
            
    @property
    def battery_temp_comp( self ):
        reg_addr = b'\xED\xF2'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response
        return response / 100
    @battery_temp_comp.setter
    def battery_temp_comp( self, value ):
        reg_addr = b'\xED\xF2'
        value = int( value * 100 )
        if value >= -100000 and value <= 100000 and value != self.ERROR_VAL:
            value = value.to_bytes( 2, byteorder='little', signed=True )
            self._write( value, 2, reg_addr, 'int' )
    
    @property
    def battery_type( self ):
        dev_cap = self.capabilities
        dev_name = self.model_name 
        reg_addr = b'\xED\xF1'
        response = self._read( 1, reg_addr, 'int' )
        
        if self.DESCRIPTIVE: 
            # Controllers without rotary switch and no load output
            # 10A/15A/20A
            if dev_cap.get( "Rotary Encoder Present" ) == "0" and dev_cap.get( "Load Output Present" ) == "0":
                if response == 1: return_value = "GEL Victron Deep Discharge"
                elif response == -1: return_value = "USER Defined"
                else: return_value = self.ERROR_VAL

            # MPPT RS Chargers
            elif dev_name.find( "MPPT RS" ) != -1: 
                if response == 1: return_value = "GEL Victron Deep Discharge (57.6V)"
                elif response == 2: return_value = "AGM Victron Deep Discharge (58.8V)"
                elif response == 3: return_value = "LiFePO4 (56.8V) With 2-Wire BMS"
                elif response == -1: return_value = "USER Defined"
                else: return_value = self.ERROR_VAL

            # Controllers with a rotary switch
            # 30A/35A/45A/50A/65A/70A/85A/100A Chargers
            elif dev_cap.get( "Rotary Encoder Present" ) == "1" or dev_cap.get( "Load Output Present" ) == "1" \
                or dev_cap.get( "Virtual Load Output " ) == "1" or dev_cap.get( "Virtual Relay" ) == "1":
                if response == 1: return_value = "GEL Victron Long Life (14.1V)"
                elif response == 2: return_value = "GEL Victron Deep Discharge (14.3V)"
                elif response == 3: return_value = "GEL Victron Deep Discharge (14.4V)"
                elif response == 4: return_value = "AGM Victron Deep Discharge (14.7V)"
                elif response == 5: return_value = "Tubular Plate Cyclic Mode 1 (14.9V)"
                elif response == 6: return_value = "Tubular Plate Cyclic Mode 2 (15.1V)"
                elif response == 7: return_value = "Tubular Plate Cyclic Mode 3 (15.3V)"
                elif response == 8: return_value = "LiFePO4 (14.2V)"
                elif response == -1: return_value = "USER Defined"
                else: return_value = self.ERROR_VAL
                
            # Catch-all for non-matched specifications according to protocol
            else:
                return_value = self.ERROR_VAL
        else: 
            return_value = response
        return return_value 
    @battery_type.setter
    def battery_type( self, value ):
        reg_addr = b'\xED\xF1'
        if value % 1 == 0 and value >= -1 and value <= 10:
            value = value.to_bytes( 1, byteorder='little', signed=True )
            self._write( value, 1, reg_addr, 'int' )

    @property
    def battery_max_curr( self ):
        reg_addr = b'\xED\xF0'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        return response / 10
    @battery_max_curr.setter
    def battery_max_curr( self, value ):
        reg_addr = b'\xED\xF0'
        value = int( value * 10 )
        if value >= 0 and value <= 10000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def battery_system_voltage( self ):
        reg_addr = b'\xED\xEF'
        return self._read( 1, reg_addr, 'int' ) 
    @battery_system_voltage.setter
    def battery_system_voltage( self, value ):
        reg_addr = b'\xED\xEF'
        value = int( value )
        if value == 12 or value == 24 or value == 36 or value == 48:
            value = value.to_bytes( 1, signed=False )
            self._write( value, 1, reg_addr, 'int' )
    
    @property
    def battery_temp( self ):
        reg_addr = b'\xED\xEC'
        response = self._read( 2, reg_addr, 'int' )
        if self.DESCRIPTIVE and response < 0: return "Not Available"
        if response >= 273.15: return response - 273.15
        return self.ERROR_VAL 

    @property
    def battery_voltage_setting( self ):
        reg_addr = b'\xED\xEA'
        return self._read( 1, reg_addr, 'int' )
    @battery_voltage_setting.setter 
    def battery_voltage_setting( self, value ):
        reg_addr = b'\xED\xEA'
        value = int( value )
        if value == 12 or value == 24 or value == 36 or value == 48:
            value = value.to_bytes( 1, signed=False )
            self._write( value, 1, reg_addr, 'int' )
    
    @property
    def battery_bms_present( self ):
        reg_addr = b'\xED\xE8'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == 0: return "NO"
            if response == 1: return "YES"
            return self.ERROR_VAL
        return response
    @battery_bms_present.setter
    def battery_bms_present( self, value ):
        reg_addr = b'\xED\xE8'
        value = int( value )
        if value == 0 or value == 1:
            value = value.to_bytes( 1, signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property
    def battery_tail_current( self ):
        reg_addr = b'\xED\xE7'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        return response / 10 
    @battery_tail_current.setter
    def battery_tail_current( self, value ):
        reg_addr = b'\xED\xE7'
        value = int( value )
        if value >= 0 and value <= 10000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def battery_low_temp_charge_curr( self ):
        reg_addr = b'\xED\xE6'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response
        if response == -1 and self.DESCRIPTITVE: return "Use Max"
        if response == -1: return self.battery_max_curr 
        return response / 10 
    @battery_low_temp_charge_curr.setter
    def battery_low_temp_charge_curr( self, value ):
        reg_addr = b'\xED\xE6'
        value = int( value * 10 )
        if value >= -1 and value <= 10000:
            value = value.to_byest( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def battery_auto_eq_stop_on_voltage( self ):
        reg_addr = b'\xED\xE5'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == 0: return "NO"
            if response == 1: return "YES"
            return self.ERROR_VAL
        return response
    @battery_auto_eq_stop_on_voltage.setter
    def battery_auto_eq_stop_on_voltage( self, value ):
        reg_addr = b'xED\xE5'
        value = int( value )
        if value == 0 or value == 1:
            value = value.to_bytes( 1, signed=False )
            self._write( value, 1, reg_addr, 'int' )
    
    @property
    def battery_equalisation_current_level( self ):
        reg_addr = b'\xED\xE4'
        return self._read( 1, reg_addr, 'int' )
    @battery_equalisation_current_level.setter
    def battery_equalisation_current_level( self, value ):
        reg_addr = b'\xED\xE4'
        value = int( value )
        if value >= 0 and value <= 100:
            value = value.to_bytes( 1, signed=True )
            self._write( value, 1, reg_addr, 'int' )

    @property
    def battery_equalisation_duration( self ):
        reg_addr = b'\xED\xE3'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response
        return response / 100
    @battery_equalisation_duration.setter
    def battery_equalisation_duration( self, value ):
        reg_addr = b'\xED\xE3'
        value = int( value * 100 )
        if value >= 0 and value <= 100000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property 
    def battery_rebulk_voltage_offset( self ):
        reg_addr = b'\xED\x2E'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response
        return response / 100
    @battery_rebulk_voltage_offset.setter
    def battery_rebulk_voltage_offset( self, value ):
        reg_addr = b'\xED\x2E'
        value = int( value * 100 )
        if value >= 0 and value <= 100000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property 
    def battery_low_temp_level( self ):
        reg_addr = b'\xED\xE0'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        return response / 100
    @battery_low_temp_level.setter
    def battery_low_temp_level( self, value ):
        reg_addr = b'\xED\xE0'
        value = int( value * 100 )
        if value >= -6000 and value <= 10000:
            value = value.to_bytes( 2, byteorder='little', signed=True )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def battery_voltage_compensation( self ):
        reg_addr = b'\xED\xCA'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response
        return response / 100
    @battery_voltage_compensation.setter
    def battery_voltage_compensation( self, value ):
        reg_addr = '\xED\xCA'
        value = int( value * 100 )
        if value >= 0 and value <= 10000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def battery_rem_input_mode_config( self ):
        dev_name = self.model_name
        reg_addr = b'\xD0\xC0'
        if dev_name.find( "MPPT RS" ) == -1:
            if self.DESCRIPTIVE:
                print( self._PREFIX + "Model does not support this command." )
            return self.ERROR_VAL
        else:
            response = self._read( 1, reg_addr, 'int' )
            if response == 0:
                if self.DESCRIPTIVE: return "Remote On/Off"
                else: return response
            elif response == 1:
                if self.DESCRIPTIVE: return "2-Wire BMS Signals"
                else: return response
            else: return self.ERROR_VAL
    @battery_rem_input_mode_config.setter
    def battery_rem_input_mode_config( self, value ):
        reg_addr = b'\xD0\xC0'
        value = int( value )
        if value == 0 or value == 1: 
            value = value.to_bytes( 1, signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property
    def battery_wire_input_states( self ):
        dev_name = self.model_name
        reg_addr = b'\xD0\x1F'
        if dev_name.find( "MPPT RS" ) == -1:
            if self.DESCRIPTIVE:
                print( self._PREFIX + "Model does not support this command." )
            return self.ERROR_VAL
        else:
            response = self._read( 1, reg_addr, 'int' )
            if response == self.ERROR_VAL: return response
            else:
                wire_dict = {}
                wire_name = [ "2-Wire BMS Input Enabled", \
                              "Allow to Discharge Active", \
                              "Allow to Charge Active", 
                              "4", "5", "6", "7", "8" ]
                wire_flag = self._bit_array( response, 8 )
        
                len_flags = len( wire_flag ) - 1
                for i in range( len( wire_name ) ):
                    wire_dict[ wire_name[i] ] = wire_flag[ len_flags - i ][-1:]
                
                return wire_dict
#-------------------------------------------------------------------------------

#--------------------------------- Charger Data --------------------------------
    # 0xEDEC Battery Temperature is listed in the Protocol DOcument here, but
    # it first appears in the battery settings sections, so it is omitted here.
    @property 
    def charger_max_curr( self ):
        reg_addr = b'\xED\xDF'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response
        return response / 10

    @property 
    def system_yield( self ):
        reg_addr = b'\xED\xDF'
        response = self._read( 4, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response == -1 and self.DESCRIPTIVE: return "Not Available" 
        if response == -1: return self.ERROR_VAL 
        if response < 0: return ( response + 4294967295 ) / 100
        return response / 100

    @property
    def user_yield( self ):
        reg_addr = b'\xED\xEC'
        response = self._read( 4, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response == -1 and self.DESCRIPTIVE: return "Not Available" 
        if response == -1: return self.ERROR_VAL 
        if response < 0: return ( response + 4294967295 ) / 100
        return response / 100

    @property
    def charger_internal_temp( self ):
        reg_addr = b'\xED\xDB'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        return response / 100

    @property 
    def charger_error_code( self ):
        reg_addr = b'\xED\xDA'
        response = self._read( 1, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        else:
            if self.DESCRIPTIVE:
                if response == 0: return "No Error!"
                if response == 2: return "Battery voltage too high!"
                if response >= 3 and response <= 5: return "Battery temp sensor issue!" 
                if response >= 6 and response <= 8: return "Battery voltage sensor issue!"
                if response == 14: return "Battery temp too low!"
                if response == 17: return "Charger internal temp too high!"
                if response == 18: return "Charger excessive output current!"
                if response == 19: return "Charger current polarity reversed!"
                if response == 20: return "Charger bulk time expired (>10Hrs)!"
                if response == 21: return "Charger current sensor issue, biasing!"
                if response == 22 or response == 23: return "Charger internal temp sensor issue!"
                if response == 26: return "Charger terminals overheated!"
                if response == 27: return "Charger short-circuit!"
                if response == 28: return "Converter issue (one of the converters is not working)!"
                if response == 29: return "Battery over-charge protection!"
                if response == 33: return "Input voltage too hight!"
                if response == 34: return "Input excessive current!"
                if response == 38: return "Input shutdown due to excessive battery voltage!"
                if response == 39: return "Input shutdown due to current flowing while converter is switched off!"
                if response == 66: return "Incompatible device in the network!"
                if response == 67: return "BMS connection lost!"
                if response == 68: return "Network misconfigured (e.g. combined ESS & ve.smart)!"
                if response == 116: return "Calibration data lost!"
                if response == 117: return "Incompatible firmware (i.e. not for this model)!"
                if response == 119: return "Settings data invalid/corrupted (use restore to defaults to reset to recover)!"
                else: return "Unknown Error Code " + str( response )
            else:
                return response 
        
    @property 
    def charger_current( self ):
        dev_name = self.model_name 
        reg_addr = b'\xED\xD7'
        if dev_name.find( "MPPT RS" ) != -1:
            if self.DESCRIPTIVE:
                print( self._PREFIX + "Model does not support this command, use dc_battery_current instead." )
            return self.ERROR_VAL
        else:
            response = self._read( 2, reg_addr, 'int' )
            if response == self.ERROR_VAL: return response 
            return response / 10

    @property 
    def charger_voltage( self ):
        dev_name = self.model_name 
        reg_addr = b'\xED\xD5'
        if dev_name.find( "MPPT RS" ) != -1:
            if self.DESCRIPTIVE:
                print( self._PREFIX + "Model does not support this command, use dc_battery_voltage instead." )
            return self.ERROR_VAL
        else:
            response = self._read( 2, reg_addr, 'int' )
            if response == self.ERROR_VAL: return response 
            return response / 100

    @property
    def charger_addtl_info( self ):
        reg_addr = b'\xED\xD4'
        dict_info = {}
        dict_names = [ "Safe Mode Active", "Automatic Equalisation Active", "2", \
                       "3", "Temperature Dimming Active", "5", \
                       "Input Current Dimming Active", "7", "8" ]
        dict_flags = self._bit_array( self._read( 1, reg_addr, 'int' ), 8 )

        if self.DESCRIPTIVE and len( dict_flags ) > 1 :
            len_flags = len( dict_flags ) - 1
            for i in range( len ( dict_names ) ):
                dict_info[ dict_names[i] ] = dict_flags[ len_flags - i ][-1:]
            return dict_info
        else:
            return dict_flags

    @property
    def yield_today( self ):
        reg_addr = b'\xED\xD3'
        response = self._read( 1, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response < 0: return ( response + 65535 ) / 100
        return response  / 100
    
    @property
    def max_power_today( self ):
        reg_addr = b'\xED\xD2'
        response = self._read( 1, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response < 0: return response + 65535
        return response 

    @property 
    def yield_yesterday( self ):
        reg_addr = b'\xED\xD1'
        response = self._read( 1, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response < 0: return ( response + 65535 ) / 100
        return response  / 100

    @property
    def max_power_yesterday( self ):
        reg_addr = b'\xED\xD0'
        response = self._read( 1, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response < 0: return response + 65535
        return response 
    
    @property
    def voltage_settings_range( self ):
        reg_addr = b'\xED\xCE'
        response = self._read( 1, reg_addr, 'b' )
        if response == self.ERROR_VAL: return response 
        min_volt = int.from_bytes( response[:-1], byteorder='big', signed=False )
        max_volt = int.from_bytes( response[-1:], byteorder='big', signed=False )
        return [min_volt,max_volt]

    @property
    def history_version( self ):
        reg_addr = b'\xED\xCD'
        return self._read( 1, reg_addr, 'int' )

    @property
    def streetlight_version( self ):
        reg_addr = b'\xED\xCC'
        return self._read( 1, reg_addr, 'int' )
    
    @property
    def equalise_current_max( self ):
        dev_name = self.model_name
        reg_addr = b'\xED\xC7'
        if dev_name.find( "MPPT RS" ) == -1:
            if self.DESCRIPTIVE:
                print( self._PREFIX + "Model does not support this command." )
            return self.ERROR_VAL
        else:
            return self._read( 1, reg_addr, 'int' )

    @property 
    def equalise_voltage_max( self ):
        dev_name = self.model_name
        reg_addr = b'\xED\xC6'
        if dev_name.find( "MPPT RS" ) == -1:
            if self.DESCRIPTIVE:
                print( self._PREFIX + "Model does not support this command." )
            return self.ERROR_VAL
        else:
            response = self._read( 1, reg_addr, 'int' )
            if response == self.ERROR_VAL: return response
            return response / 100
        
    @property
    def adjustable_voltage_min( self ):
        reg_addr = b'\x22\x11'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response
        return response / 100
    
    @property
    def adjustable_voltage_max( self ):
        reg_addr = b'\x22\x12'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response
        return response / 100
    
    @property 
    def dc_battery_ripple_voltage( self ):
        dev_name = self.model_name 
        reg_addr = b'\xED\x8B'
        if dev_name.find( "MPPT RS" ) == -1:
            if self.DESCRIPTIVE:
                print( self._PREFIX + "Model does not support this command." )
            return self.ERROR_VAL
        else:
            response = self._read( 2, reg_addr, 'int' )
            if response == self.ERROR_VAL: return response 
            if response < 0: return ( response + 65536 ) / 100
            return response / 100
        
    @property
    def dc_battery_voltage( self ):
        dev_name = self.model_name
        reg_addr = b'\xED\x8D'
        if dev_name.find( "MPPT RS" ) == -1:
            if self.DESCRIPTIVE:
                print( self._PREFIX + "Model does not support this command use charger_voltage instead." )
            return self.ERROR_VAL
        else:
            response = self._read( 2, reg_addr, 'int' )
            if response == self.ERROR_VAL: return response 
            return response / 100        

    @property
    def dc_battery_current( self ):
        dev_name = self.model_name
        reg_addr = b'\xED\x8F'
        if dev_name.find( "MPPT RS" ) == -1:
            if self.DESCRIPTIVE:
                print( self._PREFIX + "Model does not support this command, use charger_current instead." )
            return self.ERROR_VAL
        else:
            response = self._read( 2, reg_addr, 'int' )
            if response == self.ERROR_VAL: return response 
            return response / 10
#-------------------------------------------------------------------------------

#------------------------------- Solar Panel Data ------------------------------
    @property 
    def num_mppt_tracker( self ):
        dev_name = self.model_name 
        reg_addr = b'\x02\x44'
        if dev_name.find( "MPPT RS" ) == -1:
            if self.DESCRIPTIVE:
                print( self._PREFIX + "Model does not support this command." )
            return self.ERROR_VAL
        else:
            response = self._read( 1, reg_addr, 'int' )
            if response == self.ERROR_VAL: return response 
            if response < 0: return ( response + 256 )
            return response 

    @property 
    def panel_maximum_current( self ):
        reg_addr = b'\xED\xBF'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response < 0: return ( response + 65536 ) / 10
        return response / 10
    
    @property
    def panel_power( self ):
        reg_addr = b'\xED\xBC'
        response = self._read( 4, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response < 0: return ( response + 4294967296 ) / 100
        return response / 100
    
    @property
    def panel_voltage( self ):
        reg_addr = b'\xED\xBB'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response == -1 and self.DESCRIPTIVE: return "Not Available"
        if response == -1: return self.ERROR_VAL 
        if response < 0: return ( response + 65536 ) / 100
        return response / 100
    
    @property
    def panel_current( self ):
        reg_addr = b'\xED\xBD'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response < 0: return ( response + 65536 ) / 10
        return response / 10
    
    @property
    def panel_max_allowed_voltage( self ):
        reg_addr = b'\xED\xB8'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response < 0: return ( response + 65536 ) / 100
        return response / 100
    
    @property
    def tracker_mode( self ):
        reg_addr = b'\xED\xB3'
        response = self._read( 1, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if self.DESCRIPTIVE:
            if response == 0: return "OFF"
            if response == 1: return "Voltage/Current limited"
            if response == 2: return "MPP Tracker"
            return self.ERROR_VAL
        else: return response

    @property
    def panel_start_volt( self ):
        dev_name = self.model_name 
        reg_addr = b'\xED\xB2'
        if dev_name.find( "MPPT RS" ) == -1:
            if self.DESCRIPTIVE:
                print( self._PREFIX + "Model does not support this command." )
            return self.ERROR_VAL
        else:
            response = self._read( 2, reg_addr, 'int' )
            if response == self.ERROR_VAL: return response 
            if response < 0: return ( response + 65536 ) / 100
            return response / 100

    @property
    def panel_input_resistance( self ):
        dev_name = self.model_name 
        reg_addr = b'\xED\xB1'
        if dev_name.find( "MPPT RS" ) == -1:
            if self.DESCRIPTIVE:
                print( self._PREFIX + "Model does not support this command." )
            return self.ERROR_VAL
        else:
            response = self._read( 4, reg_addr, 'int' )
            if response == self.ERROR_VAL: return response 
            if response < 0: return ( response + 4294967296 )
            return response 

    @property
    def panel_power_multitrack( self ):
        return_value = []
        dev_name = self.model_name 
        num_trackers = self.num_mppt_tracker
        reg_addr = [ b'\xEC\xCC', b'\xEC\xDC', b'\xEC\xEC', b'\xEC\xFC' ]

        if dev_name.find( "MPPT RS" ) == -1:
            if self.DESCRIPTIVE:
                print( self._PREFIX + "Model does not support this command." )
            return self.ERROR_VAL
        else:
            for i in range( num_trackers ):
                response = self._read( 4, reg_addr[i], 'int' )
                if response == self.ERROR_VAL: return_value.append( response )
                elif response < 0: return_value.append( ( response + 4294967296 ) / 100 ) 
                else: return_value.append( response / 100 )
            return return_value 
                
    @property
    def panel_voltage_multitrack( self ):
        return_value = []
        dev_name = self.model_name 
        num_trackers = self.num_mppt_tracker
        reg_addr = [ b'\xEC\xCB', b'\xEC\xDB', b'\xEC\xEB', b'\xEC\xFB' ]

        if dev_name.find( "MPPT RS" ) == -1:
            if self.DESCRIPTIVE:
                print( self._PREFIX + "Model does not support this command." )
            return self.ERROR_VAL
        else:
            for i in range( num_trackers ):
                response = self._read( 2, reg_addr[i], 'int' )
                if response == self.ERROR_VAL: return_value.append( response )
                elif response < 0: return_value.append( ( response + 65536 ) / 100 ) 
                else: return_value.append( response / 100 )
            return return_value 
        
    @property
    def panel_current_multitrack( self ):
        return_value = []
        dev_name = self.model_name 
        num_trackers = self.num_mppt_tracker
        reg_addr = [ b'\xEC\xCD', b'\xEC\xDD', b'\xEC\xED', b'\xEC\xFD' ]

        if dev_name.find( "MPPT RS" ) == -1:
            if self.DESCRIPTIVE:
                print( self._PREFIX + "Model does not support this command." )
            return self.ERROR_VAL
        else:
            for i in range( num_trackers ):
                response = self._read( 2, reg_addr[i], 'int' )
                if response == self.ERROR_VAL: return_value.append( response )
                elif response < 0: return_value.append( ( response + 65536 ) / 10 ) 
                else: return_value.append( response / 10 )
            return return_value 
        
    @property
    def tracker_mode_multitrack( self ):
        return_value = []
        dev_name = self.model_name 
        num_trackers = self.num_mppt_tracker
        reg_addr = [ b'\xEC\xC3', b'\xEC\xD3', b'\xEC\xE3', b'\xEC\xF3' ]

        if dev_name.find( "MPPT RS" ) == -1:
            if self.DESCRIPTIVE:
                print( self._PREFIX + "Model does not support this command." )
            return self.ERROR_VAL
        else:
            for i in range( num_trackers ):
                response = self._read( 2, reg_addr[i], 'int' )
                if self.DESCRIPTIVE:
                    if response == 0: return_value.append( "OFF" )
                    elif response == 1: return_value.append( "Voltage/Current limited" )
                    elif response == 2: return_value.append( "MPP Tracker" )
                    else: return_value.append( self.ERROR_VAL )
                else: return_value.append( response )
        return return_value 
#-------------------------------------------------------------------------------

#--------------------------- Load Output Data/Settings -------------------------
    @property 
    def load_current( self ):
        reg_addr = b'\xED\xAD'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response
        if response < 0: return ( response + 65536 ) / 10 
        return response / 10 
    
    @property
    def load_offset_voltage( self ):
        reg_addr = b'\xED\xAC'
        response = self._read( 1, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response
        if response < 0: return ( response + 256 ) / 100 
        return response / 100
    @load_offset_voltage.setter
    def load_offset_voltage( self, value ):
        reg_addr = b'\xED\xAC'
        value = int( value * 100 )
        if value >= 0 and value <= 100000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
    
    @property
    def load_output_control( self ):
        reg_addr = b'\xED\xAB'
        response = self._read( 1, reg_addr, 'int' )       
        if response == self.ERROR_VAL: return response
        if self.DESCRIPTIVE:
            if response == 0: return "OFF"
            if response == 1: return "AUTO"
            if response == 2: return "ALT1"
            if response == 3: return "ALT2"
            if response == 4: return "ON"
            if response == 5: return "USER1"
            if response == 6: return "USER2"
            if response == 7: return "AES"
            return self.ERROR_VAL
        else: return response
    @load_output_control.setter
    def load_output_control( self, value ):
        reg_addr = b'\xED\xAB'
        try:
            if value >= 0 and value <= 7 and value == int( value ): 
                value = value 
        except: 
            try: 
                if   value.upper() == "OFF":   value = 0
                elif value.upper() == "AUTO":  value = 1
                elif value.upper() == "ALT1":  value = 2
                elif value.upper() == "ALT2":  value = 3
                elif value.upper() == "ON":    value = 4
                elif value.upper() == "USER1": value = 5
                elif value.upper() == "USER2": value = 6
                elif value.upper() == "AES":   value = 7
            except: pass
        value = value.to_bytes( 1, signed=False )
        response = self._write( value, 1, reg_addr, 'int' )

    @property 
    def load_output_voltage( self ):
        reg_addr = b'\xED\xAB'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response < 0: return (response + 65536 ) / 100
        return response / 100
    @load_output_voltage.setter
    def load_output_voltage( self, value ):
        reg_addr = b'\xED\xAB'
        value = int( value * 100 )
        if value >= 0 and value <= 100000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def load_output_state( self ):
        reg_addr = b'\xED\xA8'
        response = self._read( 1, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response
        if self.DESCRIPTIVE:
            if response == 0: return "OFF"
            if response == 1: return "ON"
            return self.ERROR_VAL
        else: return response

    @property 
    def load_switch_high_level( self ):
        reg_addr = b'\xED\x9D'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response < 0: return (response + 65536 ) / 100
        return response / 100
    @load_switch_high_level.setter
    def load_switch_high_level( self, value ):
        reg_addr = b'\xED\x9D'
        value = int( value * 100 )
        if value >= 0 and value <= 10000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property 
    def load_switch_low_level( self ):
        reg_addr = b'\xED\x9C'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response < 0: return (response + 65536 ) / 100
        return response / 100
    @load_switch_low_level.setter
    def load_switch_low_level( self, value ):
        reg_addr = b'\xED\x9C'
        value = int( value * 100 )
        if value >= 0 and value <= 10000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def load_output_off_reason( self ):
        reg_addr = b'\xED\x91'
        dict_off = {}
        dict_names = [ "Battery Low", "Short Circuit", "Timer Program", \
                       "Remote Input (VE.Direct Rx pin alternate function)", \
                       "Pay-as-you-go out of credit", "5", "6", \
                       "Device starting up" ]
        dict_flags = self._bit_array( self._read( 1, reg_addr, 'int' ), 8 )
        if dict_flags == self.ERROR_VAL: return dict_flags

        len_flags = len( dict_flags ) - 1
        for i in range( len( dict_names ) ):
            dict_off[ dict_names[i] ] = dict_flags[ len_flags - i ][-1:]    

        return dict_off

    @property
    def load_aes_timer( self ):
        reg_addr = b'\xED\x90'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response < 0: return (response + 65536 )
        return response
    @load_aes_timer.setter
    def load_aes_timer( self, value ):
        reg_addr = b'\xED\x90'
        value = int( value )
        if value >= 0 and value <= 10000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )
#-------------------------------------------------------------------------------

#-------------------------------- Relay Settings -------------------------------
    @property 
    def relay_opmode( self ):
        reg_addr = b'\xED\xD9'
        response = self._read( 1, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if self.DESCRIPTIVE:
            if response == 0: return "Relay Always Off"
            if response == 1: return "Panel Voltage High"
            if response == 2: return "Internal Temp Too High"
            if response == 3: return "Battery Voltage Too low"
            if response == 4: return "Equalisation Active"
            if response == 5: return "Error Condition Present"
            if response == 6: return "Internal Temp Too Low"
            if response == 7: return "Battery Voltage Too High"
            if response == 8: return "Charger in Float or Storage"
            if response == 9: return "Day Detection (Panels Irradiated)"
            if response == 10: return "Load Control (Switches According to Load Control Mode)"
            return self.ERROR_VAL
        else:
            return response 
    @relay_opmode.setter 
    def relay_opmode( self, value ):
        reg_addr = b'\xED\xD9'
        value = int( value )
        if value >= 0 and value <= 10:
            value = value.to_bytes( 1, signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property
    def relay_battery_low_voltage_set( self ):
        reg_addr = b'\x03\x50'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response < 0: return ( response + 65536 ) / 100
        return response / 100
    @relay_battery_low_voltage_set.setter
    def relay_battery_low_voltage_set( self, value ):
        reg_addr = b'\x03\x50'
        value = int( value * 100 )
        if value >= 0 and value <= 10000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )
    
    @property 
    def relay_battery_low_voltage_clear( self ):
        reg_addr = b'\x03\x51'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response < 0: return ( response + 65536 ) / 100
        return response / 100
    @relay_battery_low_voltage_clear.setter 
    def relay_battery_low_voltage_clear( self, value ):
        reg_addr = b'\x03\x51'
        value = int( value * 100 )
        if value >= 0 and value <= 10000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )
    
    @property
    def relay_battery_high_voltage_set( self ):
        reg_addr = b'\x03\x52'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response < 0: return ( response + 65536 ) / 100
        return response / 100
    @relay_battery_high_voltage_set.setter
    def relay_battery_high_voltage_set( self, value ):
        reg_addr = b'\x03\x52'
        value = int( value * 100 )
        if value >= 0 and value <= 10000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )
    
    @property 
    def relay_battery_high_voltage_clear( self ):
        reg_addr = b'\x03\x53'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response < 0: return ( response + 65536 ) / 100
        return response / 100   
    @relay_battery_high_voltage_clear.setter
    def relay_battery_high_voltage_clear( self, value ):
        reg_addr = b'\x03\x53'
        value = int( value * 100 )
        if value >= 0 and value <= 10000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )
    
    @property
    def relay_panel_high_voltage_set( self ):
        reg_addr = b'\xED\xBA'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response < 0: return ( response + 65536 ) / 100
        return response / 100
    @relay_panel_high_voltage_set.setter
    def relay_panel_high_voltage_set( self, value ):
        reg_addr = b'\xED\xBA'
        value = int( value * 100 )
        if value >= 0 and value <= 100000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )
    
    @property 
    def relay_panel_high_voltage_clear( self ):
        reg_addr = b'\xED\xB9'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response < 0: return ( response + 65536 ) / 100
        return response / 100
    @relay_panel_high_voltage_clear.setter
    def relay_panel_high_voltage_clear( self, value ):
        reg_addr = b'\xED\xB9'
        value = int( value * 100 )
        if value >= 0 and value <= 100000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )
    
    @property
    def relay_min_enabled_time( self ):
        reg_addr = b'\x10\x0A'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response < 0: return ( response + 65536 )
        return response
    @relay_min_enabled_time.setter
    def relay_min_enabled_time( self, value ):
        reg_addr = b'\x10\x0A'
        value = int( value )
        if value >= 0 and value <= 100000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )
#-------------------------------------------------------------------------------

#-------------------------- Lighting Controller Timer --------------------------
    @property 
    def lighting_timer_events( self ):
        reg_addr = [ b'\xED\xA0', b'\xED\xA1', b'\xED\xA2', b'\xED\xA3', \
                     b'\xED\xA4', b'\xED\xA5' ]
        return_values = []
        dict_names = [ "Time offset", "Anchor Point", "Dim Action" ]
        dict_units = [ "[min]", "[n/a]", "[%]"]

        for i in range( len( reg_addr ) ):
            dict_events = {}
            dict_vals = []
            response = self._read( 4, reg_addr[i], 'b' )
            if response == self.ERROR_VAL:
                for j in range( 3 ): dict_vals.append( response )
            else:
                time_offset = response[:-2]
                anchor_point = int.from_bytes( response[-3:-2], byteorder='big', signed=False )
                dim_action = response[-4:-3]

                dict_vals.append( int.from_bytes( time_offset, byteorder='big', signed=True ) )
                if self.DESCRIPTIVE:
                    if anchor_point == 0: dict_vals.append( "N/A" )
                    elif anchor_point == 1: dict_vals.append( "SUNSET" )
                    elif anchor_point == 2: dict_vals.append( "MID-NIGHT" )
                    elif anchor_point == 3: dict_vals.append( "SUNRISE" )
                    else: dict_vals.append( self.ERROR_VAL )
                else: 
                    dict_vals.append( anchor_point )
                dict_vals.append( int.from_bytes( dim_action, byteorder='big', signed=False ) )

                if self.DESCRIPTIVE:
                    for j in range( len( dict_names ) ):
                        dict_events[ dict_names[j] ] = [dict_vals[j], dict_units[j]]   
                    return_values.append( dict_events )
                else:
                    return_values.append( dict_vals )

        return return_values
    @lighting_timer_events.setter
    def lighting_timer_events( self, values=[] ):
        reg_addr = [ b'\xED\xA0', b'\xED\xA1', b'\xED\xA2', b'\xED\xA3', \
                     b'\xED\xA4', b'\xED\xA5' ]
        if len( values ) == 6:
            index = 0
            for events in values:
                time_offset = int( events[0] )
                anchor_point = int( events[1] )
                dim_action = int( events[2] )

                good_vals = True
                if time_offset < -1440 or time_offset > 1440: good_vals = False 
                if anchor_point < 1 or anchor_point > 3: good_vals = False
                if dim_action < 0 or anchor_point > 100: good_vals = False 

                if good_vals: 
                    time_offset = time_offset.to_bytes( 2, byteorder='big', signed=True )
                    anchor_point = anchor_point.to_bytes( 1, signed=False )
                    dim_action = dim_action.to_bytes( 1, signed=False )
                    timer_event = dim_action + anchor_point + time_offset
                    timer_event = self._flip( timer_event )
                    self._write( timer_event, 4, reg_addr[index], 'int' )
                index += 1

    @property
    def lighting_midpoint_shift( self ):
        reg_addr = b'\xED\xA7'
        return self._read( 2, reg_addr, 'int' )
    @lighting_midpoint_shift.setter
    def lighting_midpoint_shift( self, value ):
        reg_addr = b'\xED\xA7'
        value = int( value )
        if value >= -24 and value <= 24:
            value = value.to_bytes( 2, byteorder='little', signed=True )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def lighting_gradual_dim_speed( self ):
        reg_addr = b'\xED\x9B'
        response = self._read( 1, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response < 0: return response + 256
        return response 
    @lighting_gradual_dim_speed.setter
    def lighting_gradual_dim_speed( self, value ):
        reg_addr = b'\xED\x9B'
        value = int( value )
        if value >= 0 and value <= 255:
            value = value.to_bytes( 1, signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property
    def lighting_panel_voltage_night( self ):
        reg_addr = b'\xED\x9A'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response < 0: return ( response + 65536 ) / 100 
        return response / 100 
    @lighting_panel_voltage_night.setter 
    def lighting_panel_voltage_night( self, value ):
        reg_addr = b'\xED\x9A'
        value = int( value * 100 )
        if value >= 0 and value <= 100000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def lighting_panel_voltage_day( self ):
        reg_addr = b'\xED\x99'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response < 0: return ( response + 65536 ) / 100 
        return response / 100 
    @lighting_panel_voltage_day.setter
    def lighting_panel_voltage_day( self, value ):
        reg_addr = b'\xED\x99'
        value = int( value * 100 )
        if value >= 0 and value <= 100000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' ) 

    @property
    def lighting_sunset_delay( self ):
        reg_addr = b'\xED\x96'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response < 0: return response + 65536  
        return response 
    @lighting_sunset_delay.setter
    def lighting_sunset_delay( self, value ):
        reg_addr = b'\xED\x96'
        value = int( value )
        if value >= 0 and value <= 10000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def lighting_sunrise_delay( self ):
        reg_addr = b'\xED\x97'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response < 0: return response + 65536  
        return response 
    @lighting_sunrise_delay.setter
    def lighting_sunrise_delay( self, value ):
        reg_addr = b'\xED\x97'
        value = int( value )
        if value >= 0 and value <= 10000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def lighting_aes_timer( self ):
        reg_addr = b'\xED\x90'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response < 0: return response + 65536  
        return response 
    @lighting_aes_timer.setter
    def lighting_aes_timer( self, value ):
        reg_addr = b'\xED\x90'
        value = int( value )
        if value >= 0 and value <= 10000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def lighting_solar_activity( self ):
        reg_addr = b'\x20\x30'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == 0: return "DARK"
            if response == 1: return "LIGHT"
            return self.ERROR_VAL
        return response 

    @property
    def lighting_time_of_day( self ):
        reg_addr = b'\x20\x31'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response == -1 and self.DESCRIPTIVE: return "Not Available"
        if response == -1: return self.ERROR_VAL
        if response < 0: return response + 65536  
        return response 
    @lighting_time_of_day.setter
    def lighting_time_of_day( self, value ):
        reg_addr = b'\x20\x31'
        value = int( value )
        if value >= 0 and value <= 10000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )
#-------------------------------------------------------------------------------

#--------------------------- VE.Direct Port Functions --------------------------
    @property
    def tx_port_opmode( self ):
        reg_addr = b'\xED\x9E'
        response = self._read( 1, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response
        if self.DESCRIPTIVE:
            if response == 0: return "Normal VE.Direct Communication (default)"
            if response == 1: return "Pulse for every 0.01kWh harvested (100ms low)"
            if response == 2: return "Lighting control pwm normal (f=160Hz, 0%=0V)"
            if response == 3: return "Lighting control pwm inverted (f=160Hz, 0%=5V)"
            if response == 4: return "Virtual load output"
            return self.ERROR_VAL
        else: return response 
    @tx_port_opmode.setter
    def tx_port_opmode( self, value ):
        reg_addr = b'\xED\x9E'
        value = int( value )
        if value >= 0 and value <= 4:
            value = value.to_bytes( 1, signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property 
    def rx_port_opmode( self ):
        reg_addr = b'\xED\x98'
        response = self._read( 1, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response
        if self.DESCRIPTIVE:
            if response == 0: return "Remote On/Off"
            if response == 1: return "Load output configuration"
            if response == 2: return "Load output on/off remote control (inverted)"
            if response == 3: return "Load output on/off remote control (normal)"
            return self.ERROR_VAL
        else: return response 
    @rx_port_opmode.setter
    def rx_port_opmode( self, value ):
        reg_addr = b'\xED\x98'
        value = int( value )
        if value >= 0 and value <= 3:
            value = value.to_bytes( 1, signed=False )
            self._write( value, 1, reg_addr, 'int' )
#-------------------------------------------------------------------------------

#------------------------ Pluggable Display Functions --------------------------
    @property 
    def disp_backlight_mode( self ):
        device_type = self.model_name
        if device_type.find( "MPPT RS" ) != -1: reg_addr = b'\x04\x08'
        else: reg_addr = b'\x04\x00'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == 0: return "KEYPRESS"
            if response == 1: return "ON"
            if response == 2: return "AUTO"
            return "UNKNOWN MODE"
        else: return response   
    @disp_backlight_mode.setter
    def disp_backlight_mode( self, value ):
        device_type = self.model_name
        if device_type.find( "MPPT RS" ) != -1: reg_addr = b'\x04\x08'
        else: reg_addr = b'\x04\x00'
        value = int( value )
        if value >= 0 and value <= 3:
            value = value.to_bytes( 1, signed=False )
            self._write( value, 1, reg_addr, 'int' )        

    @property 
    def disp_backlight_intensity( self ):
        reg_addr = b'\x04\x01'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == 0: return "ALWAYS OFF"
            if response == 1: return "ON"
            return "UNKNOWN INTENSITY SETTING"
        else: return response 
    @disp_backlight_intensity.setter
    def disp_backlight_intensity( self, value ):
        reg_addr = b'\x04\x01'
        value = int( value )
        if value == 0 or value == 1:
            value = value.to_bytes( 1, signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property
    def disp_scroll_speed( self ):
        reg_addr = b'\x04\x02'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == 1: return "SLOW"
            if response == 2: return "SLOW MEDIUM"
            if response == 3: return "MEDIUM"
            if response == 4: return "MEDIUM FAST"
            if response == 5: return "FAST"
            return "UNKNOWN SCROLL SPEED"
        else: return response 
    @disp_scroll_speed.setter
    def disp_scroll_speed( self, value ):
        reg_addr = b'\x04\x02'
        value = int( value )
        if value >= 1 and value <= 5:
            value = value.to_bytes( 1, signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property
    def disp_setup_lock( self ):
        reg_addr = b'\x04\x03'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == 0: return "UNLOCKED"
            if response == 1: return "LOCKED"
            return "UNKNOWN"
        else: return response
    @disp_setup_lock.setter
    def disp_setup_lock( self, value ):
        reg_addr = b'\x04\x03'
        value = int( value )
        if value == 0 or value == 1:
            value = value.to_bytes( 1, signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property 
    def disp_temp_units( self ):
        reg_addr = b'\x04\x04'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == 0: return "CELSIUS"
            if response == 1: return "FARENHEIT"
            return "UNKNOWN"
        else: return response 
    @disp_temp_units.setter
    def disp_temp_units( self, value ):
        reg_addr = b'\x04\x04'
        value = int( value )
        if value == 0 or value == 1:
            value = value.to_bytes( 1, signed=False )
            self._write( value, 1, reg_addr, 'int' )
#-------------------------------------------------------------------------------

#------------------------- Internal Display Functions --------------------------
    @property 
    def disp_contrast( self ):
        reg_addr = b'\x04\x06'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == 0: return "0"
            if response == 1: return "1"
            if response == 2: return "2"
            if response == 3: return "3"
            if response == 4: return "4"
            if response == 5: return "5"
            return "UNKNOWN"
        else: return response 
    @disp_contrast.setter
    def disp_contrast( self, value ):
        reg_addr = b'\x04\x06'
        value = int( value )
        if value >= 0 and value <= 5: 
            value = value.to_bytes( 1, signed=False )
            self._write( value, 1, reg_addr, 'int' )
#-------------------------------------------------------------------------------

#-------------------------- Remote Control Functions ---------------------------
    @property
    def rm_charge_algorithm( self ):
        reg_addr = b'\x20\x00'
        response = self._read( 1, reg_addr, 'int' )
        return response 
    @rm_charge_algorithm.setter
    def rm_charge_algorithm( self, value ):
        reg_addr = b'\x20\x00'
        value = int( value )
        if value >= 0 and value <= 255:
            value = value.to_bytes( 1, signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property
    def rm_charge_voltage_setpoint( self ):
        reg_addr = b'\x20\x01'
        response = self._read( 1, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response
        if response == -1: return self.ERROR_VAL
        return response / 100
    @rm_charge_voltage_setpoint.setter
    def rm_charge_voltage_setpoint( self, value ):
        reg_addr = b'\x20\x01'
        value = int( value * 100 )
        if value >= 0 and value <= 100000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' ) 
    
    @property
    def rm_battery_voltage_sense( self ):
        reg_addr = b'\x20\x02'
        response = self._read( 1, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response == -1: return self.ERROR_VAL
        return response / 100 
    @rm_battery_voltage_sense.setter
    def rm_battery_voltage_sense( self, value ):
        reg_addr = b'\x20\x02'
        value = int( value * 100 )
        if value >= 0 and value <= 100000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' ) 

    @property
    def rm_battery_temp_sense( self ):
        reg_addr = b'\x20\x03'
        response = self._read( 1, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response == int.from_bytes( b'\x7F\xFF', byteorder='big', signed=True ): return self.ERROR_VAL
        return response / 100 
    @rm_battery_temp_sense.setter
    def rm_battery_temp_sense( self, value ):
        reg_addr = b'\x20\x03'
        value = int( value * 100 )
        if value >= -100000 and value <= 100000:
            value = value.to_bytes( 2, byteorder='little', signed=True )
            self._write( value, 2, reg_addr, 'int' ) 

    @property
    def remote_command( self ):
        # it's write only.
        print( self._PREFIX + "This property is write only?" )
        return self.ERROR_VAL
    @remote_command.setter
    def remote_command( self, value ):
        reg_addr = b'\x20\x04'
        value = int( value )
        if value >= 1 and value <= 4:
            value = value.to_bytes( 1, signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property 
    def rm_charge_state_elapsed_time( self ):
        reg_addr = b'\x20\x07'
        response = self._read( 4, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        return response / 1000
    
    @property
    def rm_absorption_time( self ):
        reg_addr = b'\x20\x08'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        return response / 100
    @rm_absorption_time.setter
    def rm_absorption_time( self, value ):
        reg_addr = b'\x20\x08'
        value = int( value * 100 )
        if value >= 0 and value <= 100000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def rm_error_code( self ):
        reg_addr = b'\x20\x09'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == 0: return "0"
            if response == 1: return "1"
            if response == 2: return "2"
            if response == 3: return "3"
            if response == 4: return "4"
            if response == 5: return "5"
            return "UNKNOWN"
        else: return response 

    @property 
    def rm_battery_charge_current( self ):
        reg_addr = b'\x20\x0A'
        response = self._read( 4, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response == 4294967295: return self.ERROR_VAL
        return response / 1000
    @rm_battery_charge_current.setter
    def rm_battery_charge_current( self, value ):
        reg_addr = b'\x20\x0A'
        value = int( value * 1000 )
        if value >= -1000000 and value <= 10000000:
            value = value.to_bytes( 4, byteorder='little', signed=True )
            self._write( value, 4, reg_addr, 'int' )

    @property
    def rm_battery_idle_voltage( self ):
        reg_addr = b'\x20\x0B'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        return response / 100 
    @rm_battery_idle_voltage.setter
    def rm_battery_idle_voltage( self, value ):
        reg_addr = b'\x20\x0B'
        value = int( value * 100 )
        if value >= 0 and value <= 100000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property 
    def rm_device_state( self ):
        reg_addr = b'\x20\x0C'
        response = self._read( 1, reg_addr, 'int' )
        if self.DESCRIPTIVE:
            if response == -11: return "WAKE-UP"                #=245
            if response == -10: return "REPEATED ABSORPTION"    #=246
            if response == -9: return "AUTO EQUALISE"           #=247
            if response == -8: return "BATTERY SAFE"            #=248
            if response == -7: return "LOAD DETECT"             #=249
            if response == -4: return "EXTERNAL CONTROL"        #=252
            if response == -1: return "UNAVAILABLE"             #=255
            if response == 0: return "NOT CHARGING"
            if response == 2: return "FAULT"
            if response == 3: return "BULK"
            if response == 4: return "ABSORPTION"
            if response == 5: return "FLOAT"
            if response == 6: return "STORAGE"
            if response == 7: return "MANUAL EQUALISE"
            if response == 11: return "POWER SUPPLY"
            return "UNKNOWN"
        else: return response 
    @rm_device_state.setter
    def rm_device_state( self, value ):
        reg_addr = b'\x20\x0C'
        value = int( value )
        if value >= 0 and value <= 255:
            value = value.to_bytes( 1, signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property
    def rm_network_info( self ):
        reg_addr = b'\x20\x0D'
        response = self._read( 1, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response
        else:
            net_dict = {}
            net_name = [ "BMS Control", "Remote Voltage Set-Point",
                         "Charge Slave", "Charge Master", "ICharge",
                         "ISense", "TSense", "VSense", "Standby" ] 
        
            net_flag = self._bit_array( response, 8 )
        
            len_flags = len( net_flag ) - 1
            for i in range( len( net_name ) ):
                net_dict[ net_name[i] ] = net_flag[ len_flags - i ][-1:]
        
            return net_dict
    
    @property 
    def rm_network_mode( self ):
        reg_addr = b'\x20\x0E'
        response = self._read( 1, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response
        else:
            net_dict = {}
            net_name = [ "Networked", "Slave Mode", "External Control Mode",
                        "BMS Controlled", "Charge Group Master", 
                        "Charge Instance Master", "Standby", "Reserved" ] 
            
            net_flag = self._bit_array( response, 8 )
            
            len_flags = len( net_flag ) - 1
            for i in range( len( net_name ) ):
                net_dict[ net_name[i] ] = net_flag[ len_flags - i ][-1:]
            
            return net_dict
    @rm_network_mode.setter
    def rm_network_mode( self, value_bits=[0,0,0,0,0,0,0,0] ):
        reg_addr = b'\x20\x0E'
        # value[0] -> value[7] = bit7 -> bit0
        value = 0
        for i in range( 8 ):
            int_value = int_value | value_bits[7-i]
            if i != 7: value = value << 1
        value = value.to_bytes( 1, signed=False )
        self._write( value, 1, reg_addr, 'int' )

    @property
    def rm_network_status( self ):
        reg_addr = b'\x20\x0F'
        response = self._read( 1, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response
        else:
            net_dict = {}
            net_dict["Status"] = ""
            net_name = [ "Status", "ICharge", "ISense", "TSense", "VSense" ]
            net_vals = self._bit_array( response, 8 )

            len_vals = len( net_vals ) - 1
            for i in range( len( net_name ) ):
                if i == 0:
                    for j in range( 4 ):
                        net_dict[ net_name[i] ] = net_dict.get( net_name[i] ) + net_vals[ len_vals - ( i + j ) ][-1:]
                else:
                    net_dict[ net_name[i] ] = net_vals[ len_vals - ( i + 3 ) ][-1:]
            return net_dict 

    @property
    def rm_total_charge_current( self ):
        reg_addr = b'\x20\x13'
        response = self._read( 4, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        else: return response / 1000
    @rm_total_charge_current.setter
    def rm_total_charge_current( self, value ):
        reg_addr = b'\x20\x13'
        value = int( value * 1000 )
        if value >= -100000000 and value <= 1000000000:
            value = value.to_bytes( 4, byteorder='little', signed=True )
            self._write( value, 4, reg_addr, 'int')

    @property 
    def rm_charge_current_percentage( self ):
        reg_addr = b'\x20\x14'
        response = self._read( 4, reg_addr, 'int' )
        return response 
    @rm_charge_current_percentage.setter
    def rm_charge_current_percentage( self, value ):
        reg_addr = b'\x20\x14'
        value = int( value )
        if value >= 0 and value <= 100:
            value = value.to_bytes( 1, signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property
    def rm_charge_current_limit( self ):
        reg_addr = b'\x20\x15'
        response = self._read( 2, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response 
        if response == -1: return self.ERROR_VAL
        else: return response / 10
    @rm_charge_current_limit.setter
    def rm_charge_current_limit( self, value ):
        reg_addr = b'\x20\x15'
        value = int( value * 10 )
        if value >= 0 and value <= 100000:
            value = value.to_bytes( 2, byteorder='little', signed=False )
            self._write( value, 2, reg_addr, 'int' )

    @property
    def rm_manual_equalisation_pending( self ):
        reg_addr = b'\x20\x18'
        response = self._read( 1, reg_addr, 'int' )
        return response 
    @rm_manual_equalisation_pending.setter
    def rm_manual_equalisation_pending( self, value ):
        reg_addr = b'\x20\x18'
        value = int( value )
        if value >= 0 and value <= 255:
            value = value.to_bytes( 1, signed=False )
            self._write( value, 1, reg_addr, 'int' )

    @property
    def rm_total_dc_input_power( self ):
        reg_addr = b'\x20\x27'
        response = self._read( 4, reg_addr, 'int' )
        if response == self.ERROR_VAL: return response
        else: return response / 100
    @rm_total_dc_input_power.setter
    def rm_total_dc_input_power( self, value ):
        reg_addr = b'\x20\x27'
        value = int( value * 100 )
        if value >= 0 and value <= 10000000000:
            value = value.to_bytes( 4, byteorder='little', signed=False )
            self._write( value, 4, reg_addr, 'int' )
#-------------------------------------------------------------------------------
#===============================================================================

#=========================== Data History Functions ============================
#------------------------------- total_history ---------------------------------
    def total_history( self ):
        reg_addr = b'\x10\x4F'
        tot_dict = {}
        tot_name = [ "Reserved 0", "Error Database", "Error 0", 
                     "Error 1", "Error 2", "Error 3", "User Total Yield", 
                     "System Total Yield", "Panel Voltage Maximum", 
                     "Battery Voltage Maximum", "Number of Available Days" ]
        
        tot_vals = ""
        tot_vals = self._read( 33, reg_addr, 'b' )
        
        pos = 0
        index = 0
        if tot_vals[:1] == b'\x00':
            skip = [1,1,1,1,1,1,4,4,2,2,1]
            d_places = [0,0,0,0,0,0,2,2,2,2,0]
            while index < len( skip ): 
                tot_dict[ tot_name[index] ] = int.from_bytes( tot_vals[pos:(pos+skip[index])], byteorder='little', signed=False ) / ( 10 ** d_places[index] )
                pos += skip[index]
                index += 1      
        elif tot_vals[:1] == b'\x01':
            tot_name.append( "Battery Voltage Minimum" )
            for i in range( 13 ): tot_name.append( "Reserved " + str( i + 1 ) )
            skip = [1,1,1,1,1,1,4,4,2,2,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1]
            d_places = [0,0,0,0,0,0,2,2,2,2,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0]
            while index < len( skip ): 
                tot_dict[ tot_name[index] ] = int.from_bytes( tot_vals[pos:(pos+skip[index])], byteorder='little', signed=False ) / ( 10 ** d_places[index] )
                pos += skip[index]
                index += 1
        else: return self.ERROR_VAL

        return tot_dict
#-------------------------------------------------------------------------------
#-------------------------------- day_record -----------------------------------
    def _day_record( self, reg_addr ):
        day_dict = {}
        day_name = [ "Reserved", "Yield", "Consumed", "Battery Voltage Maximum",
                     "Battery Voltage Minimum", "Error Database", "Error 0", 
                     "Error 1", "Error 2", "Error 3", "Time Bulk", "Time Absorption",
                     "Time Float", "Power Maximum", "Battery Current Maximum", 
                     "Panel Voltage Maximum", "Day Sequence Number" ]
        skip = [1,4,4,2,2,1,1,1,1,1,2,2,2,4,2,2,2]
        d_places = [0,2,2,2,2,0,0,0,0,0,0,0,0,0,1,2,0]

        day_vals = ""
        day_vals = self._read( 33, reg_addr, 'b' )

        pos = 0
        index = 0 
        while index < len( skip ): 
            if d_places[index] == 0:
                day_dict[ day_name[index] ] = int.from_bytes( day_vals[pos:(pos+skip[index])], byteorder='little', signed=False )
            else:
                day_dict[ day_name[index] ] = int.from_bytes( day_vals[pos:(pos+skip[index])], byteorder='little', signed=False ) / ( 10 ** d_places[index] )
            pos += skip[index]
            index += 1 
        
        return day_dict 
#-------------------------------------------------------------------------------
#------------------------------ get_all_history --------------------------------
    def get_all_history( self ):
        all_history = []
        base_reg = int.from_bytes( b'\x10\x50', byteorder='big', signed=False )
        n_days = int( self.total_history().get( "Number of Available Days" ) )
        
        if n_days > 0:
            for i in range( n_days ):
                reg_addr = ( base_reg + i ).to_bytes( 2, byteorder='big', signed=False )
                day_history = self._day_record( reg_addr ) 
                all_history.append( day_history )

        return all_history
#-------------------------------------------------------------------------------
#------------------------------ get_last_history -------------------------------
    def get_last_history( self ):
        return self._day_record( b'\x10\x50' ) 
#-------------------------------------------------------------------------------
#------------------------------- get_one_history -------------------------------
    def get_one_history( self, n_days_ago ):
        base_reg = int.from_bytes( b'\x10\x50', byteorder='big', signed=False )
        n_days = int( self.total_history().get( "Number of Available Days" ) )

        if n_days_ago <= n_days: 
            reg_addr = ( base_reg + n_days_ago ).to_bytes( 2, byteorder='big', signed=False )
            return self._day_record( reg_addr )
        else:
            print( self._PREFIX + "Only " + str( n_days ) + " days of history exists, you requested history for " + str( n_days_ago ) + " days ago?" ) 
            return self.ERROR_VAL
#-------------------------------------------------------------------------------
#------------------------------- day_mppt_record -------------------------------
    def _day_mppt_record( self, reg_addr ):
        day_dict = {}
        day_name = [ "Reserved 0", "Day Sequence Number", "Energy Tracker 1", 
                     "Energy Tracker 2", "Energy Tracker 3", "Energy Tracker 4",
                     "Peak Power Tracker 1", "Peak Power Tracker 2", "Peak Power Tracker 3",
                     "Peak Power Tracker 4", "Voc Max Tracker 1", "Voc Max Tracker 2",
                     "Voc Max Tracker 3", "Voc Max Tracker 4" ]
        for i in range(9): day_name.append( "Reserved " + str( i + 1 ) )
        skip = [1,2,2,2,2,2,2,2,2,2,2,2,2,2,1]
        d_places = [0,0,2,2,2,2,0,0,0,0,2,2,2,2,0]

        day_vals = ""
        day_vals = self._read( 37, reg_addr, 'b' )

        pos = 0
        index = 0 
        while index < len( skip ): 
            if d_places[index] == 0:
                day_dict[ day_name[index] ] = int.from_bytes( day_vals[pos:(pos+skip[index])], byteorder='little', signed=False )
            else:
                day_dict[ day_name[index] ] = int.from_bytes( day_vals[pos:(pos+skip[index])], byteorder='little', signed=False ) / ( 10 ** d_places[index] )
            pos += skip[index]
            index += 1 
        
        return day_dict 
#-------------------------------------------------------------------------------
#----------------------------- get_all_mppt_history ----------------------------
    def get_all_mppt_history( self ):
        all_mppt_history = []
        base_reg = int.from_bytes( b'\x10\xA0', byteorder='big', signed=False )
        n_days = int( self.total_history().get( "Number of Available Days" ) )
        
        if n_days > 0:
            for i in range( n_days ):
                reg_addr = ( base_reg + i ).to_bytes( 2, byteorder='big', signed=False )
                day_mppt_history = self._day_mppt_record( reg_addr ) 
                all_mppt_history.append( day_mppt_history )

        return all_mppt_history
#-------------------------------------------------------------------------------
#----------------------------- get_last_mppt_history ---------------------------
    def get_last_mppt_history( self ):
        return self._day_mppt_record( b'\x10\xA0' ) 
#-------------------------------------------------------------------------------
#----------------------------- get_one_mppt_history ----------------------------
    def get_one_mppt_history( self, n_days_ago ):
        base_reg = int.from_bytes( b'\x10\xA0', byteorder='big', signed=False )
        n_days = int( self.total_history().get( "Number of Available Days" ) )

        if n_days_ago <= n_days: 
            reg_addr = ( base_reg + n_days_ago ).to_bytes( 2, byteorder='big', signed=False )
            return self._day_mppt_record( reg_addr )
        else:
            print( self._PREFIX + "Only " + str( n_days ) + " days of mppt history exists, you requested mppt history for " + str( n_days_ago ) + " days ago?" ) 
            return self.ERROR_VAL
#-------------------------------------------------------------------------------
#===============================================================================

#================================ Basic Functions ==============================
#------------------------------------ ping -------------------------------------
    def ping( self ):
        response = self._send_cmd( "1" )
        if response == self.ERROR_VAL: return response 
        else: return ( response - 16384 ) / 100 
#-------------------------------------------------------------------------------
#----------------------------------- restart -----------------------------------
    def restart( self ):
        response = self._send_cmd( "6" )
        if response == "RESTART": 
            print( self._PREFIX + "Succesfully issued restart command." )
            time.sleep( 3 )
        else: print( self._PREFIX + "Failed to send the restart command.")
#-------------------------------------------------------------------------------
#----------------------------- application_version -----------------------------
    def application_version( self ):
        response = self._send_cmd( "3" )
        if response == self.ERROR_VAL: return response 
        else: return ( response - 16384 ) / 100 
#-------------------------------------------------------------------------------
#------------------------------ restore_to_default -----------------------------
    def restore_to_default( self ):
        reg_addr = b'\x00\x04'
        reg_data = b'\x00\x00' #ignored anyways
        self._write( reg_data, 2, reg_addr, 'int' )
#-------------------------------------------------------------------------------
#--------------------------------- clear_history -------------------------------
    def clear_history( self ):
        reg_addr = b'\x10\x30'
        reg_data = b'\x00\x00' #ignored?
        self._write( reg_data, 2, reg_addr, 'int' )
#-------------------------------------------------------------------------------
#===============================================================================

# Tester Function for direct call
if __name__ == '__main__':
    mppt = vedirect( 'COM8' )
    mppt.DEBUG = True
    #mppt.readall

    # 0x01** product information registers
    #print( mppt.PREFIX + "VE.Direct device product id = " + str( mppt.pid ) )
    #print( mppt.PREFIX + "VE.Direct device group id = " + str( mppt.group_id) )
    #print( mppt.PREFIX + "VE.Direct device serial number = " + str( mppt.serial_number ) )
    #print( mppt.PREFIX + "VE.Direct device model name = " + str( mppt.model_name ) )
    #for key,value in mppt.capabilities.items(): print( mppt.PREFIX + key + " = " + str( value ) )

    # 0x02** device control registers
    #print( mppt.PREFIX + "VE.Direct device mode = " + str( mppt.device_mode ) )
    #print( mppt.PREFIX + "VE.Direct device state = " + str( mppt.device_state ) )
    #print( mppt.PREFIX + "Remote Control used = " + str( mppt.remote_control ) )
    #print( mppt.PREFIX + "VE.Direct device off reason = " + str( mppt.device_off_reason ) )
    
    # Battery settings registers
    #print( mppt.PREFIX + "Batterysafe mode = " + str( mppt.batterysafe_mode ) )
    #print( mppt.PREFIX + "Adaptive mode = " + str( mppt.adaptive_mode ) )
    #print( mppt.PREFIX + "Automatic equalisation mode = " + str( mppt.automatic_equalisation_mode ) )
    #print( mppt.PREFIX + "Battery bulk time limit = " + str( mppt.battery_bulk_time_limit ) + " [hours].")
    #print( mppt.PREFIX + "Battery absorption time limit = " + str( mppt.battery_absorption_time_limit ) + " [hours]." )
    #print( mppt.PREFIX + "Battery absorption voltage = " + str( mppt.battery_absorption_voltage ) + " [V].")
    #print( mppt.PREFIX + "Battery float voltage = " + str( mppt.battery_float_voltage ) + " [V].")
    #print( mppt.PREFIX + "Battery equalisation voltage = " + str( mppt.battery_equalisation_voltage ) + " [V].")
    #print( mppt.PREFIX + "Battery temperature compensation = " + str( mppt.battery_temp_comp) + " [mV/K]. ")
    #print( mppt.PREFIX + "Battery type = " + str( mppt.battery_type ) )
    #print( mppt.PREFIX + "Battery maximum current = " + str( mppt.battery_max_curr ) + " [A]." )
    #print( mppt.PREFIX + "Battery system voltage = " + str( mppt.battery_voltage ) + " [V]." )
    #print( mppt.PREFIX + "Battery temperature = " + str( mppt.battery_temp ) + " [°C].")
    #print( mppt.PREFIX + "Battery voltage setting = " + str( mppt.battery_voltage_setting ) + " [V]." )
    #print( mppt.PREFIX + "Battery BMS Present = " + str( mppt.battery_bms_present ) )
    #print( mppt.PREFIX + "Battery tail current = " + str( mppt.battery_tail_current ) )
    #print( mppt.PREFIX + "Battery low temperature charge current = " + str( mppt.battery_low_temp_charge_curr ) + " [A].")
    #print( mppt.PREFIX + "Battery Auto equalise stop on voltage = " + str( mppt.battery_auto_eq_stop_on_voltage ) )
    #print( mppt.PREFIX + "Battery equalisation current level = " + str( mppt.battery_equalisation_current_level ) + " [% of 0xEDF0]." )
    #print( mppt.PREFIX + "Battery equalisation duration = " + str( mppt.battery_equalisation_duration ) + " [hours]." )
    #print( mppt.PREFIX + "Battery re-bulk voltage offset = " + str( mppt.battery_rebulk_voltage_offset ) + " [V].")
    #print( mppt.PREFIX + "Battery low temperature level = " + str( mppt.battery_low_temp_level ) + " [°C].")
    #print( mppt.PREFIX + "Battery voltage compensation = " + str( mppt.battery_voltage_compensation ) + " [V].")

    # Charger Data
    #print( mppt.PREFIX + "Battery temperature (duplicate) = " + str( mppt.battery_temp) + " [°C]." )
    #print( mppt.PREFIX + "Charger maximum current = " + str( mppt.charger_max_curr ) + " [A]." )
    #print( mppt.PREFIX + "System yield = " + str( mppt.system_yield ) + " [kWh]." )
    #print( mppt.PREFIX + "User yield (resettable) = " + str( mppt.user_yield ) + " [kWh]." )
    #print( mppt.PREFIX + "Charger internal temperature = " + str( mppt.charger_internal_temp ) + " [°C]." )
    #print( mppt.PREFIX + "Charger error code = " + str( mppt.charger_error_code ) )
    #print( mppt.PREFIX + "Charger current = " + str( mppt.charger_current ) + " [A]." )
    #print( mppt.PREFIX + "Charger voltage = " + str( mppt.charger_voltage ) + " [V]." )
    #print( mppt.PREFIX + "Charger additional information = " + str( mppt.charger_addtl_info ) )
    #print( mppt.PREFIX + "Yield today = " + str( mppt.yield_today ) + " [kWh]." )
    #print( mppt.PREFIX + "Max power today = " + str( mppt.max_power_today ) + " [W]." )
    #print( mppt.PREFIX + "Yield yesterday = " + str( mppt.yield_yesterday ) + " [kWh].")
    #print( mppt.PREFIX + "Max power yesterday = " + str( mppt.max_power_yesterday ) + " [W]." )
    #print( mppt.PREFIX + "Voltage settings range [min, max] = " + str( mppt.voltage_settings_range) + " [V]." )
    #print( mppt.PREFIX + "Charger history version = " + str( mppt.history_version ) )
    #print( mppt.PREFIX + "Charger streetlight version = " + str( mppt.streetlight_version ) )
    #print( mppt.PREFIX + "Equalise current maximum = " + str( mppt.equalise_current_max ) + " [A]." )
    #print( mppt.PREFIX + "Equalise voltage maximum = " + str( mppt.equalise_voltage_max ) + " [V]." )
    #print( mppt.PREFIX + "Adjustable voltage minimum = " + str( mppt.adjustable_voltage_min ) + " [V]." )
    #print( mppt.PREFIX + "Adjustable voltage maximum = " + str( mppt.adjustable_voltage_max ) + " [V]." )
    #print( mppt.PREFIX + "DC channel battery ripple voltage = " + str( mppt.dc_battery_ripple_voltage ) + " [V]." )
    #print( mppt.PREFIX + "DC channel battery voltage = " + str( mppt.dc_battery_voltage ) + " [V]." )
    #print( mppt.PREFIX + "DC channel battery current = " + str( mppt.dc_battery_current ) + " [V]." )

    # Solar Panel Data
    #print( mppt.PREFIX + "Number of MPPT trackers = " + str( mppt.num_mppt_tracker ) )
    #print( mppt.PREFIX + "Panel maximum current = " + str( mppt.panel_maximum_current ) + " [A]." )
    #print( mppt.PREFIX + "Panel power = " + str( mppt.panel_power ) + " [W]." )
    #print( mppt.PREFIX + "Panel voltage = " + str( mppt.panel_voltage ) + " [V]." )
    #print( mppt.PREFIX + "Panel current = " + str( mppt.panel_current ) + " [A]." )
    #print( mppt.PREFIX + "Panel maximum allowable voltage = " + str( mppt.panel_max_allowed_voltage ) + " [V]." )
    #print( mppt.PREFIX + "Tracker mode = " + str( mppt.tracker_mode ) )
    #print( mppt.PREFIX + "Panel starting voltage = " + str( mppt.panel_start_volt ) + " [V]." )
    #print( mppt.PREFIX + "Panel input resistance = " + str( mppt.panel_input_resistance ) + " [Ohm]." )
    #print( mppt.PREFIX + "Panel power multiple trackers = " + str( mppt.panel_power_multitrack ) + " [W]." )
    #print( mppt.PREFIX + "Panel power multiple trackers = " + str( mppt.panel_voltage_multitrack ) + " [V]." )
    #print( mppt.PREFIX + "Panel power multiple trackers = " + str( mppt.panel_current_multitrack ) + " [A]." )
    #print( mppt.PREFIX + "Panel power multiple trackers = " + str( mppt.tracker_mode_multitrack ) )

    # Load Output Data/Settings
    #print( mppt.PREFIX + "Load current = " + str( mppt.load_current ) + " [A]." )
    #print( mppt.PREFIX + "Load offset voltage = " + str( mppt.load_offset_voltage ) + " [V]." )
    #print( mppt.PREFIX + "Load output control = " + str( mppt.load_output_control ) )
    #print( mppt.PREFIX + "Load output voltage = " + str( mppt.load_output_voltage ) + " [V]." )
    #print( mppt.PREFIX + "Load output state = " + str( mppt.load_output_state )  )
    #print( mppt.PREFIX + "Load switch high level = " + str( mppt.load_switch_high_level ) + " [V]." )
    #print( mppt.PREFIX + "Load switch low level = " + str( mppt.load_switch_low_level ) + " [V]." )
    #print( mppt.PREFIX + "Load output off reason = " + str( mppt.load_output_off_reason ) )
    #print( mppt.PREFIX + "Load automatic energy selector (aes) timer = " + str( mppt.load_aes_timer ) + " [min]." )

    # Relay Settings
    #print( mppt.PREFIX + "Relay operation mode = " + str( mppt.relay_opmode ) )
    #print( mppt.PREFIX + "Relay battery low voltage set = " + str( mppt.relay_battery_low_voltage_set ) + " [V]." )
    #print( mppt.PREFIX + "Relay battery low voltage clear = " + str( mppt.relay_battery_low_voltage_clear ) + " [V]." )
    #print( mppt.PREFIX + "Relay battery high voltage set = " + str( mppt.relay_battery_high_voltage_set ) + " [V]." )
    #print( mppt.PREFIX + "Relay battery high voltage clear = " + str( mppt.relay_battery_high_voltage_clear ) + " [V]." )
    #print( mppt.PREFIX + "Relay panel high voltage set = " + str( mppt.relay_panel_high_voltage_set ) + " [V]." )
    #print( mppt.PREFIX + "Relay panel high voltage clear = " + str( mppt.relay_panel_high_voltage_clear ) + " [v]." )
    #print( mppt.PREFIX + "Relay minimum enabled time = " + str( mppt.relay_min_enabled_time ) + " [min]." )

    # Lighting Controller Timer
    #print( mppt.PREFIX + "Lighting controller timer events = " + str( mppt.lighting_timer_events ) )
    #print( mppt.PREFIX + "Lighting controller mid-point shift = " + str( mppt.lighting_midpoint_shift ) + " [min]." )
    #print( mppt.PREFIX + "Lighting controller gradual dim speed = " + str( mppt.lighting_gradual_dim_speed) + " [s]." )
    #print( mppt.PREFIX + "Lighting controller nighttime panel voltage = " + str( mppt.lighting_panel_voltage_night ) + " [V]." )
    #print( mppt.PREFIX + "Lighting controller daytime panel voltage = " + str( mppt.lighting_panel_voltage_day ) + " [V]." )
    #print( mppt.PREFIX + "Lighting controller sunset time delay = " + str( mppt.lighting_sunset_delay ) + " [min]." )
    #print( mppt.PREFIX + "Lighting controller sunrise time delay = " + str( mppt.lighting_sunrise_delay ) + " [min]." )
    #print( mppt.PREFIX + "Lighting controller AES timer = " + str( mppt.lighting_aes_timer ) + " [min]." )
    #print( mppt.PREFIX + "Lighting controller solar activity = " + str( mppt.lighting_solar_activity )  )
    #print( mppt.PREFIX + "Lighting controller time of day = " + str( mppt.lighting_time_of_day ) + " [min]." )

    # VE.Direct Port Functions
    #print( mppt.PREFIX + "Tx port operation mode = " + str( mppt.tx_port_opmode ) )
    #print( mppt.PREFIX + "Rx port operation mode = " + str( mppt.rx_port_opmode ) )

    # History Data, history data for MPPT RS controllers is accessed via "    "_mppt_history functions.
    #for key,value in mppt.total_history().items(): print( mppt.PREFIX + key + " = " + str( value ) )
    #for key,value in mppt.get_last_history().items(): print( mppt.PREFIX + key + " = " + str( value ) )
    #for key,value in mppt.get_one_history( 23 ).items(): print( mppt.PREFIX + key + " = " + str( value ) )
    # this one takes some time...
    #for daily_history in mppt.get_all_history():
    #    print( "-----------------------------------------------------------------")
    #    for key,value in daily_history.items(): print( mppt.PREFIX + key + " = " + str( value ) )
    #    print( "-----------------------------------------------------------------")

    # Basic commands
    #mppt.restore_to_default()
    #mppt.restart() 
    #print( mppt.PREFIX + "Ping response = " + str( mppt.ping() ) + ", which is the application version." )
    #print( mppt.PREFIX + "Application version = " + str( mppt.application_version() ) + "." )
    #mppt.clear_history()

    # Display Settings
    #print( mppt.PREFIX + "Display backlight mode = " + str( mppt.disp_backlight_mode ) )
    #print( mppt.PREFIX + "Display backlight intensity = " + str( mppt.disp_backlight_intensity ) )
    #print( mppt.PREFIX + "Display scroll text speed = " + str( mppt.disp_scroll_speed ) )
    #print( mppt.PREFIX + "Display setup lock = " + str( mppt.disp_setup_lock ) )
    #print( mppt.PREFIX + "Display temperature units = " + str( mppt.disp_temp_units ) )
    #print( mppt.PREFIX + "Display contrast = " + str( mppt.disp_contrast ) )

    # Networking...
    #print( mppt.PREFIX + "Remote charge algorithm version = " + str( mppt.rm_charge_algorithm ) )
    #print( mppt.PREFIX + "Remote battery voltage setpoint = " + str( mppt.rm_charge_voltage_setpoint ) + " [V]." )
    #print( mppt.PREFIX + "Remote battery voltage sense = " + str( mppt.rm_battery_voltage_sense ) + " [V]." )
    #print( mppt.PREFIX + "Remote battery temperature sense = " + str( mppt.rm_battery_temp_sense ) + " [°C]." )
    #print( mppt.PREFIX + "Remote command = " + str( mppt.remote_command ) )
    #print( mppt.PREFIX + "Remote charge state elapsed time = " + str( mppt.rm_charge_state_elapsed_time ) + " [ms]." )
    #print( mppt.PREFIX + "Remote absorption time = " + str( mppt.rm_absorption_time ) + " [hours]." )
    #print( mppt.PREFIX + "Remote error code = " + str( mppt.rm_error_code ) + " [code]." )
    #print( mppt.PREFIX + "Remote battery charge current = " + str( mppt.rm_battery_charge_current ) + " [A]." )
    #print( mppt.PREFIX + "Remote battery idle voltage = " + str( mppt.rm_battery_idle_voltage ) + " [V]." )
    #print( mppt.PREFIX + "Remote device state = " + str( mppt.rm_device_state ) )
    #for key,value in mppt.rm_network_info.items(): print( mppt.PREFIX + key + " = " + str( value ) )
    #for key,value in mppt.rm_network_mode.items(): print( mppt.PREFIX + key + " = " + str( value ) )
    #for key,value in mppt.rm_network_status.items(): print( mppt.PREFIX + key + " = " + str( value ) )
    #print( mppt.PREFIX + "Remote total charge current = " + str( mppt.rm_total_charge_current ) + " [A]." )
    #print( mppt.PREFIX + "Remote charge current percentage = " + str( mppt.rm_charge_current_percentage ) + " [%]." )
    #print( mppt.PREFIX + "Remote charge current limit = " + str( mppt.rm_charge_current_limit ) + " [A]." )
    #print( mppt.PREFIX + "Remote manual equalisation pending = " + str( mppt.rm_manual_equalisation_pending ) )
    #print( mppt.PREFIX + "Remote total DC input power = " + str( mppt.rm_total_dc_input_power ) + " [W]." )