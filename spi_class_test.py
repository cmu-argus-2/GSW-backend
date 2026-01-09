# lets test the spi class
from lib.rfmspi import RFMSPI
import lib.argus_fsk_consts as REG

radio_spi = RFMSPI(0, 0, 5000000)


# read the version
version = radio_spi.read_u8(address=REG._VERSION) 
print(f"Version: {version:#02x}")
