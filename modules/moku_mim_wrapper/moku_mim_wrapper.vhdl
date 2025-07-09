-- ///////////////Documentation////////////////////
-- This is a module that resembles the environment
-- of Moku MultiInstrument Mode, which enables
-- the use of multiple MCC instruments from the
-- last project.
-- MIM configs of different architectures are
-- simultaneously instantiated in the design,
-- each instantiates multiple MCCs according
-- to the config file from the last project.
-- It's the upper level module's responsibility
-- to multiplex between the different architectures.
-- Refer to config.xml from the last project to check the id.
-- Must keep the contents consistent.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity moku_mim_wrapper is
    generic(
        io_buf : buf_type := buf_for_io
    );
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        core_param_in   :   in  std_logic_vector(2047 downto 0);
        inputa          :   in  std_logic_vector(15 downto 0);
        inputb          :   in  std_logic_vector(15 downto 0);
        inputc          :   in  std_logic_vector(15 downto 0);
        inputd          :   in  std_logic_vector(15 downto 0);
        outputa         :   out std_logic_vector(15 downto 0);
        outputb         :   out std_logic_vector(15 downto 0);
        outputc         :   out std_logic_vector(15 downto 0);
        outputd         :   out std_logic_vector(15 downto 0)
    );
end entity moku_mim_wrapper;

architecture id_12 of moku_mim_wrapper is
begin
    slot_2 : entity work.mcc_wrapper(pdh) port map(
        clk             =>  clk,
        rst             =>  rst,
        core_param_in   =>  core_param_in(1023 downto 512),
        inputa          =>  inputa,
        inputb          =>  x"0000",
        outputa         =>  outputa,
        outputb         =>  outputb,
        outputc         =>  outputc,
        outputd         =>  open
    );
end architecture id_12;
