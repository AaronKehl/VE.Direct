# VE.Direct

Victron VE.Direct Python Class Files

## BlueSolar Hex

Currently vedirect.py contains programming to interact with a Victron Solar Charge Controller.

## How It Works

With vedirect.py in your working directory you can import, then initialize a ve.direct device.
This is VERY different from current VE.Direct scripts that only retreive/decode the heartbeat from the device.  This class allows all individual parameters (if applicable) to be written/read individually.  
e.g:

- import vedirect
- mppt = vedirect( "COM8" )

## Why

I build remote systems and maintaining energy system insight is critical to my personal development and the robustness of what I design.  These types of scripts allow me to datalog system information to telemeter and/or record to file.  This type of insight shows me how well a system is performing, from an energy perspective, allows me to iterate on design aspects if they are not as robust as expected, and advise on remote system servicing.  Imagine being able to digitally control how your systems function based off of energy system components.  That's what I do! Battery state of charge too low, please go into preserve energy mode!  Battery cell temperatures too low??? Turn on that enclosure heater, but only if we have enough energy capacity or solar generation.  Etcetera, hopefully you get the picture.

## Examples

For examples of how to use the properties/functions within the class look to the dunder main portion of the Python script.  Most properties are writeable, refer to Victron's documentation at <https://www.victronenergy.com/upload/documents/BlueSolar-HEX-protocol.pdf> for further information about what VE.Direct devices are capable of doing/reporting.

### Future Works

In the future I will likely fold in other formats of VE.Direct's protocol, e.g. BMV devices.

### Final Thoughts

I am a Mechanical Engineer by trade, and thus, my programming style may not be exactly what a computer science trained individual would expect.  Nor do I always know how to provide files/directions to install these at the system/environment level.  I try to be thorough and proper, however I can't know what I don't know!  I'm sure my code can be improved, but let's not let that get in the way of bringing helpful plugins to 'market'.  Hopefully you find this helpful for your uses and hopefully I can develop further iterations of this script and generate future scripts with similar functionality. Thanks for reading!
