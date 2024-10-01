-- ///////////////Documentation////////////////////
-- Defines some constants to help manage configurations
-- for moku MIM modules.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package moku_mim_config is
    -- The max id of configurations currently integrated in the design.
    constant MAX_ID         :   integer := 6;
    -- Indicating which ids are actually instantiated in the design.
    constant VALID_ID       :   std_logic_vector(MAX_ID downto 0) := "1000011";

    -- Bus commands dedicated to the moku_mim_wrapper.
    -- The additional information contains 32 bits.
    -- Following masks are not used in the design but just provides a reference.
    constant MISC_MIM_EN_MASK : std_logic_vector(31 downto 0) := x"10000000";
    constant MISC_MIM_ID_MASK : std_logic_vector(31 downto 0) := x"0000003F";
end package moku_mim_config;