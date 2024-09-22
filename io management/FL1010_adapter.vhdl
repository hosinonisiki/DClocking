-- ///////////////Documentation////////////////////
-- Maps 2 40-pin signals to the LPC interface.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity FL1010_adapter is
    port(
        j2_40p      :   in   std_logic_vector(3 to 36);
        j3_40p      :   in   std_logic_vector(3 to 36);

        j2_40p_fmc  :   out  std_logic_vector(3 to 36);
        j3_40p_fmc  :   out  std_logic_vector(3 to 36);
        lpc240p_eeprom_iic_scl_fmc : out std_logic;
        lpc240p_eeprom_iic_sda_fmc : out std_logic
    );
end entity FL1010_adapter;

architecture structural of FL1010_adapter is
    signal eeprom_iic_scl : std_logic;
    signal eeprom_iic_sda : std_logic;
begin
    eeprom_iic_scl <= '1'; -- EEPROM part not finished yet
    eeprom_iic_sda <= '1'; -- EEPROM part not finished yet

    j2_40p_fmc <= j2_40p;
    j3_40p_fmc <= j3_40p;
    lpc240p_eeprom_iic_scl_fmc <= eeprom_iic_scl;
    lpc240p_eeprom_iic_sda_fmc <= eeprom_iic_sda;
end architecture structural;

