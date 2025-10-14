-- ///////////////Documentation////////////////////
-- Controls the sys_mmcm_sel signal. Toggles on
-- the falling edge of a debounced user key input.
-- Holds sys_mmcm_rst high for a few cycles.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity sys_mmcm_sel_ctrl is
    port(
        clk         :   in  std_logic;
        rst         :   in  std_logic;
        sys_mmcm_sel_cmd    :   in  std_logic;
        sys_mmcm_sel        :   out std_logic;
        sys_mmcm_rst        :   out std_logic
    );
end entity sys_mmcm_sel_ctrl;

architecture behavioural of  sys_mmcm_sel_ctrl is
    type state_type is (s_idle, s_rst, s_rst_1, s_switch, s_switch_1);
    signal state : state_type := s_idle;

    signal sys_mmcm_sel_cmd_1 : std_logic := '0';
    signal sys_mmcm_sel_buf : std_logic := '1';
begin
    process(clk, rst)
    begin
        if rst = '1' then
            state <= s_idle;
        else
            if rising_edge(clk) then
                case state is
                    when s_idle =>
                        if sys_mmcm_sel_cmd = '0' and sys_mmcm_sel_cmd_1 = '1' then
                            state <= s_rst;
                        end if;
                    when s_rst =>
                        state <= s_rst_1;
                    when s_rst_1 =>
                        state <= s_switch;
                    when s_switch =>
                        state <= s_switch_1;
                    when s_switch_1 =>
                        state <= s_idle;
                end case;
            end if;
        end if;
    end process;

    process(clk, rst)
    begin
        if rst = '1' then
            sys_mmcm_sel_cmd_1 <= '0';
        else
            if rising_edge(clk) then
                sys_mmcm_sel_cmd_1 <= sys_mmcm_sel_cmd;
            end if;
        end if;
    end process;

    process(clk, rst)
    begin
        if rst = '1' then
            sys_mmcm_rst <= '0';
            sys_mmcm_sel_buf <= '1';
        else
            if rising_edge(clk) then
                case state is
                    when s_idle =>
                        sys_mmcm_rst <= '0';
                    when s_rst =>
                        sys_mmcm_rst <= '1';
                    when s_rst_1 =>
                        sys_mmcm_rst <= '1';
                    when s_switch =>
                        sys_mmcm_sel_buf <= not sys_mmcm_sel_buf;
                        sys_mmcm_rst <= '1';
                    when s_switch_1 =>
                        sys_mmcm_rst <= '1';
                end case;
            end if;
        end if;
    end process;

    sys_mmcm_sel <= sys_mmcm_sel_buf;
end architecture behavioural;