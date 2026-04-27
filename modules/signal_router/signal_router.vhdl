-- ///////////////Documentation////////////////////
-- This project involves a large number of hardware
-- implemented apparatuses working on the FPGA.
-- In order to allow to connect them freely as if
-- they were real experimental devices, a router
-- module is added to direct the data flow between
-- them.

-- Each output channel is controlled by a byte where
-- last 6 bits indicate from which input port the signal
-- should be routed, the 7th indicates whether the channel
-- is enabled, and the 8th indicates whether to keep
-- the output unchaged for the sake of stable signal
-- output during changes in the routing.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity signal_router is
    generic(
        io_buf : buf_type := buf_for_io
    );
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        core_param_in   :   in  std_logic_vector(1023 downto 0);
        sig_in          :   in  signal_array(63 downto 0);
        sig_out         :   out signal_array(63 downto 0);
        ctrl_in         :   in  std_logic_vector(63 downto 0);
        ctrl_out        :   out std_logic_vector(63 downto 0)
    );
end entity signal_router;

architecture full of signal_router is
    signal sig_in_buf   :   signal_array(63 downto 0);
    signal sig_out_buf  :   signal_array(63 downto 0);
    signal ctrl_in_buf  :   std_logic_vector(63 downto 0);
    signal ctrl_out_buf :   std_logic_vector(63 downto 0);

    signal control      :   std_logic_vector(1023 downto 0);

    signal sig_out_hold_reg : signal_array(63 downto 0) := (others => (others => '0'));
    signal ctrl_out_hold_reg : std_logic_vector(63 downto 0) := (others => '0');

    constant ctrl_base_addr : integer := 512;
begin
    use_input_buffer : if io_buf = buf_for_io or io_buf = buf_i_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    sig_in_buf <= (others => (others => '0'));
                    ctrl_in_buf <= (others => '0');
                else
                    sig_in_buf <= sig_in;
                    ctrl_in_buf <= ctrl_in;
                end if;
            end if;
        end process;
    end generate;

    no_input_buffer : if io_buf = buf_o_only or io_buf = buf_none generate
        sig_in_buf <= (others => (others => '0')) when rst = '1' else sig_in;
        ctrl_in_buf <= (others => '0') when rst = '1' else ctrl_in;
    end generate;

    use_output_buffer : if io_buf = buf_for_io or io_buf = buf_o_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    sig_out <= (others => (others => '0'));
                    ctrl_out <= (others => '0');
                else
                    sig_out <= sig_out_buf;
                    ctrl_out <= ctrl_out_buf;
                end if;
            end if;
        end process;
    end generate;

    no_output_buffer : if io_buf = buf_i_only or io_buf = buf_none generate
        sig_out <= (others => (others => '0')) when rst = '1' else sig_out_buf;
        ctrl_out <= (others => '0') when rst = '1' else ctrl_out_buf;
    end generate;

    control <= core_param_in;

    routings : for i in 0 to 63 generate
        process(clk)
        begin
            if rising_edge(clk) then
                if control(i * 8 + 7) = '0' then
                    sig_out_hold_reg(i) <= sig_out_buf(i);
                end if;
                if control(i * 8 + 6) = '0' then
                    sig_out_buf(i) <= (others => '0');
                elsif control(i * 8 + 7) = '1' then
                    sig_out_buf(i) <= sig_out_hold_reg(i);
                else
                    sig_out_buf(i) <= sig_in_buf(to_integer(unsigned(control(i * 8 + 5 downto i * 8))));
                end if;
                if control(ctrl_base_addr + i * 8 + 7) = '0' then
                    ctrl_out_hold_reg(i) <= ctrl_out_buf(i);
                end if;
                if control(ctrl_base_addr + i * 8 + 6) = '0' then
                    ctrl_out_buf(i) <= '0';
                elsif control(ctrl_base_addr + i * 8 + 7) = '1' then
                    ctrl_out_buf(i) <= ctrl_out_hold_reg(i);
                else
                    ctrl_out_buf(i) <= ctrl_in_buf(to_integer(unsigned(control(ctrl_base_addr + i * 8 + 5 downto ctrl_base_addr + i * 8))));
                end if;
            end if;
        end process;
    end generate;
end architecture full;


