-- ///////////////Documentation////////////////////
-- Linearly scales & adds bias to an input signal.
-- No clamp is applied to the output.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity scaler is
    generic(
        io_buf : buf_type := buf_for_io
    );
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        core_param_in   :   in  std_logic_vector(255 downto 0);
        sig_in          :   in  std_logic_vector(15 downto 0);
        sig_out         :   out std_logic_vector(15 downto 0)
    );
end entity scaler;

architecture behavioral of scaler is
    signal sig_in_buf   :   signed(15 downto 0);
    signal sig_out_buf  :   signed(15 downto 0);

    -- Each "x" "_" "z" and "y" represents 4 bits, with the "x" aligned with final output,
    -- "y" representing dont care, "z" representing bits to be discarded and "_" representing unused bits.
    signal scale            :   signed(23 downto 0); -- Scalling factor = scale / 2^16, from 2^-16 to 2^8
    signal bias             :   signed(27 downto 0); -- yy xxxx y___
    signal product          :   signed(39 downto 0); -- yy xxxx yzzz
    signal sum_buf          :   signed(27 downto 0); -- yy xxxx y___
    signal sum_buf_limited  :   signed(27 downto 0); -- yy xxxx y___
    signal upper_limit      :   signed(27 downto 0); -- yy xxxx y___
    signal lower_limit      :   signed(27 downto 0); -- yy xxxx y___

    signal enable_wrapping  :   std_logic;
begin
    use_output_buffer : if io_buf = buf_for_io or io_buf = buf_o_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    sig_out <= (others => '0');
                else
                    sig_out <= std_logic_vector(sig_out_buf);
                end if;
            end if;
        end process;
    end generate;

    no_output_buffer : if io_buf = buf_i_only or io_buf = buf_none generate
        sig_out <= (others => '0') when rst = '1' else std_logic_vector(sig_out_buf);
    end generate;

    use_input_buffer : if io_buf = buf_for_io or io_buf = buf_i_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    sig_in_buf <= (others => '0');
                else
                    sig_in_buf <= signed(sig_in);
                end if;
            end if;
        end process;
    end generate;

    no_input_buffer : if io_buf = buf_o_only or io_buf = buf_none generate
        sig_in_buf <= (others => '0') when rst = '1' else signed(sig_in);
    end generate;

    scale <= signed(core_param_in(23 downto 0)); -- address 0x00
    bias <= (7 downto 0 => core_param_in(47)) & signed(core_param_in(47 downto 32)) & x"0"; -- address 0x01
    upper_limit <= (7 downto 0 => core_param_in(79)) & signed(core_param_in(79 downto 64)) & x"0"; -- address 0x02
    lower_limit <= (7 downto 0 => core_param_in(111)) & signed(core_param_in(111 downto 96)) & x"0"; -- address 0x03
    enable_wrapping <= core_param_in(128); -- address 0x04

    sum_buf <= product(39 downto 12) + ((26 downto 0 => '0') & product(11)) + bias;
    sum_buf_limited <= upper_limit when sum_buf > upper_limit else
                        lower_limit when sum_buf < lower_limit else
                        sum_buf;

    process(clk)
    begin
        if rising_edge(clk) then
            product <= sig_in_buf * scale;
            if enable_wrapping = '1' then
                sig_out_buf <= sum_buf(19 downto 4);
            else
                sig_out_buf <= sum_buf_limited(19 downto 4);
            end if;
        end if;
    end process;
end architecture behavioral;