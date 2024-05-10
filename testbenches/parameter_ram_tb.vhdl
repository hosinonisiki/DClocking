library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity parameter_ram_tb is
end entity;

architecture bhvr of parameter_ram_tb is
    signal clk          :   std_logic := '0';
    signal rst          :   std_logic := '1';
    signal cnt          :   integer := 0;
    signal wdata        :   std_logic_vector(dbus_w - 1 downto 0); -- Data to be written to the ram
    signal wadd         :   std_logic_vector(abus_w - 1 downto 0); -- Address to write to
    signal wmask        :   std_logic_vector(dbus_w - 1 downto 0); -- Data mask
    signal wval         :   std_logic; -- Valid signal
    signal wen          :   std_logic; -- Write enable signal. The writing process starts as soon as wen is active, but the data is only written once wval is active. 
                                       -- This is to make sure that parameters longer than dbus_w are written simultaneously.
    signal rdata        :   std_logic_vector(dbus_w - 1 downto 0); -- Data read from the ram
    signal radd         :   std_logic_vector(abus_w - 1 downto 0); -- Address to read from
    signal rval         :   std_logic; -- Valid signal, active when the data is ready
    signal ren          :   std_logic; -- Read enable signal

    constant ram_size   :   integer := 2 ** abus_w * dbus_w;
    signal ram          :   std_logic_vector(ram_size - 1 downto 0);
begin
    uut : entity work.parameter_ram port map(
        clk             =>  clk,
        rst             =>  rst,
        wdata_in        =>  wdata,
        wadd_in         =>  wadd,
        wmask_in        =>  wmask,
        wval_in         =>  wval,
        wen_in          =>  wen,
        rdata_out       =>  rdata,
        radd_in         =>  radd,
        rval_out        =>  rval,
        ren_in          =>  ren,
        ram_data_out    =>  ram
    );

    clk <= not clk after 1 ns;

    process(clk)
    begin
        if rising_edge(clk) then
            cnt <= cnt + 1;
        end if;
    end process;

    rst <= '1' when cnt <= 20 else '0';
    
    wdata <= x"0871749A" when cnt <= 100 else
                x"0983456B" when cnt <= 200 else
                x"526789AB" when cnt <= 300 else
                x"12345678" when cnt <= 400 else
                x"87654321" when cnt <= 500 else
                x"ABCDEF01" when cnt <= 600 else
                x"FEDCBA09" when cnt <= 700 else
                x"01234567" when cnt <= 800 else
                x"76543210" when cnt <= 900 else
                x"ABCDEF01" when cnt <= 1000 else
                x"1A2B3C4D" when cnt <= 1100 else
                x"2B3C4D5E" when cnt <= 1200 else
                x"3C4D5E6F" when cnt <= 1300 else
                x"4D5E6F7A" when cnt <= 1400 else
                x"5E6F7A8B" when cnt <= 1500 else
                x"6F7A8B9C" when cnt <= 1600 else
                x"7A8B9C0D" when cnt <= 1700 else
                x"8B9C0D1E" when cnt <= 1800 else
                x"9C0D1E2F" when cnt <= 1900 else
                x"0D1E2F3A" when cnt <= 2000 else
                x"1E2F3A4B" when cnt <= 2100 else
                x"2F3A4B5C" when cnt <= 2200 else
                x"3A4B5C6D" when cnt <= 2300 else
                x"4B5C6D7E" when cnt <= 2400 else
                x"5C6D7E8F" when cnt <= 2500 else
                x"6D7E8F0A" when cnt <= 2600 else
                x"7E8F0A1B" when cnt <= 2700 else
                x"8F0A1B2C" when cnt <= 2800 else
                x"0A1B2C3D" when cnt <= 2900 else
                x"1B2C3D4E" when cnt <= 3000 else
                x"00000000";

    wadd <= "00000" when cnt <= 100 else
            "10101" when cnt <= 105 else
            "01010" when cnt <= 210 else
            "11100" when cnt <= 315 else
            "00011" when cnt <= 420 else
            "10010" when cnt <= 525 else
            "01101" when cnt <= 630 else
            "10001" when cnt <= 735 else
            "01110" when cnt <= 840 else
            "00101" when cnt <= 945 else
            "11000" when cnt <= 1050 else
            "10110" when cnt <= 1155 else
            "01001" when cnt <= 1260 else
            "11101" when cnt <= 1365 else
            "00010" when cnt <= 1470 else
            "10011" when cnt <= 1575 else
            "01100" when cnt <= 1680 else
            "10000" when cnt <= 1785 else
            "01111" when cnt <= 1890 else
            "00100" when cnt <= 1995 else
            "11001" when cnt <= 2100 else
            "10111" when cnt <= 2205 else
            "01000" when cnt <= 2310 else
            "11110" when cnt <= 2415 else
            "00001" when cnt <= 2520 else
            "10000" when cnt <= 2625 else
            "01110" when cnt <= 2730 else
            "10010" when cnt <= 2835 else
            "01101" when cnt <= 2940 else
            "00110" when cnt <= 3045 else
            "11010" when cnt <= 3150 else
            "00000";

    wmask <= x"FFFFFFFF" when cnt <= 100 else
                x"FFFF0000" when cnt <= 200 else
                x"0000FFFF" when cnt <= 300 else
                x"00FF00FF" when cnt <= 400 else
                x"FF00FF00" when cnt <= 500 else
                x"0F0F0F0F" when cnt <= 600 else
                x"F0F0F0F0" when cnt <= 700 else
                x"0FF00FF0" when cnt <= 800 else
                x"F00FF00F" when cnt <= 900 else
                x"0F0F0F0F" when cnt <= 1000 else
                x"F0F0F0F0" when cnt <= 1100 else
                x"FFFFFF00" when cnt <= 1200 else
                x"00FFFFFF" when cnt <= 1300 else
                x"FF00FF00" when cnt <= 1400 else
                x"0F0F0F0F" when cnt <= 1500 else
                x"FFFF0FFF" when cnt <= 1600 else
                x"0FFF0FFF" when cnt <= 1700 else
                x"FF0FFF0F" when cnt <= 1800 else
                x"0FF0FF0F" when cnt <= 1900 else
                x"FFF0FFFF" when cnt <= 2000 else
                x"0FFF0FFF" when cnt <= 2100 else
                x"FF0FFF0F" when cnt <= 2200 else
                x"0FF0FF0F" when cnt <= 2300 else
                x"0FFFFFFF" when cnt <= 2400 else
                x"F0FFFFFF" when cnt <= 2500 else
                x"FF0FFFFF" when cnt <= 2600 else
                x"0F0FFFFF" when cnt <= 2700 else
                x"FFF0FFFF" when cnt <= 2800 else
                x"0FFF0FFF" when cnt <= 2900 else
                x"FF0FFF0F" when cnt <= 3000 else
                x"00000000";
    
    wen <= '1' when cnt <= 100 else
            '0' when cnt <= 250 else
            '1' when cnt <= 350 else
            '0' when cnt <= 700 else
            '1' when cnt <= 800 else
            '0' when cnt <= 900 else
            '1' when cnt <= 1000 else
            '0' when cnt <= 1350 else
            '1' when cnt <= 1450 else
            '0' when cnt <= 2000 else
            '1' when cnt <= 2050 else
            '0' when cnt <= 2100 else
            '1' when cnt <= 2150 else
            '0' when cnt <= 2300 else  
            '1' when cnt <= 2350 else
            '0' when cnt <= 2500 else
            '1' when cnt <= 2600 else
            '0' when cnt <= 2700 else
            '1' when cnt <= 2800 else
            '0' when cnt <= 2900 else
            '1' when cnt <= 3000 else
            '0';
    
    wval <= '1' when cnt mod 2 = 0 and cnt <= 3000 else
            '0' when cnt mod 3 = 0 and cnt <= 3000 else
            '1' when cnt mod 5 = 0 and cnt <= 3000 else
            '0' when cnt mod 7 = 0 and cnt <= 3000 else
            '1' when cnt mod 11 = 0 and cnt <= 3000 else
            '0' when cnt mod 13 = 0 and cnt <= 3000 else
            '1' when cnt mod 17 = 0 and cnt <= 3000 else
            '0' when cnt mod 19 = 0 and cnt <= 3000 else
            '1' when cnt mod 23 = 0 and cnt <= 3000 else
            '0' when cnt mod 29 = 0 and cnt <= 3000 else
            '1' when cnt mod 31 = 0 and cnt <= 3000 else
            '0' when cnt mod 37 = 0 and cnt <= 3000 else
            '1' when cnt mod 41 = 0 and cnt <= 3000 else
            '0' when cnt mod 43 = 0 and cnt <= 3000 else
            '1' when cnt mod 47 = 0 and cnt <= 3000 else
            '0' when cnt mod 53 = 0 and cnt <= 3000 else
            '1' when cnt mod 59 = 0 and cnt <= 3000 else
            '0' when cnt mod 61 = 0 and cnt <= 3000 else
            '1' when cnt mod 67 = 0 and cnt <= 3000 else
            '0' when cnt mod 71 = 0 and cnt <= 3000 else
            '1' when cnt mod 73 = 0 and cnt <= 3000 else
            '0' when cnt mod 79 = 0 and cnt <= 3000 else
            '1' when cnt mod 83 = 0 and cnt <= 3000 else
            '0' when cnt mod 89 = 0 and cnt <= 3000 else
            '1' when cnt mod 97 = 0 and cnt <= 3000 else
            '0';
    
    radd <= "00000" when cnt <= 100 else
            "00001" when cnt <= 200 else
            "00010" when cnt <= 300 else
            "00011" when cnt <= 400 else
            "00100" when cnt <= 500 else
            "00101" when cnt <= 600 else
            "00110" when cnt <= 700 else
            "00111" when cnt <= 800 else
            "01000" when cnt <= 900 else
            "01001" when cnt <= 1000 else
            "01010" when cnt <= 1100 else
            "01011" when cnt <= 1200 else
            "01100" when cnt <= 1300 else
            "01101" when cnt <= 1400 else
            "01110" when cnt <= 1500 else
            "01111" when cnt <= 1600 else
            "10000" when cnt <= 1700 else
            "10001" when cnt <= 1800 else
            "10010" when cnt <= 1900 else
            "10011" when cnt <= 2000 else
            "10100" when cnt <= 2100 else
            "10101" when cnt <= 2200 else
            "10110" when cnt <= 2300 else
            "10111" when cnt <= 2400 else
            "11000" when cnt <= 2500 else
            "11001" when cnt <= 2600 else
            "11010" when cnt <= 2700 else
            "11011" when cnt <= 2800 else
            "11100" when cnt <= 2900 else
            "11101" when cnt <= 3000 else
            "00000";

    ren <= '1' when cnt <= 100 else
            '0' when cnt <= 250 else
            '1' when cnt <= 350 else
            '0' when cnt <= 700 else
            '1' when cnt <= 800 else
            '0' when cnt <= 900 else
            '1' when cnt <= 1000 else
            '0' when cnt <= 1350 else
            '1' when cnt <= 1450 else
            '0' when cnt <= 2000 else
            '1' when cnt <= 2050 else
            '0' when cnt <= 2100 else
            '1' when cnt <= 2150 else
            '0' when cnt <= 2300 else  
            '1' when cnt <= 2350 else
            '0' when cnt <= 2500 else
            '1' when cnt <= 2600 else
            '0' when cnt <= 2700 else
            '1' when cnt <= 2800 else
            '0' when cnt <= 2900 else
            '1' when cnt <= 3000 else
            '0';

end architecture bhvr;
