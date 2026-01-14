-- ///////////////Documentation////////////////////
-- SCALO stands for self-calibrating local oscillator.
-- This module is intended to serve as the controller
-- in a lock-in system where the frequency of the
-- incoming signal is first identified and then used
-- to calibrate a local oscillator to match that frequency.
-- The state machine keeps tracking the frequency and,
-- once triggered, adds the difference to the LO incremental
-- phase and enables a PID controller.
-- The state machine takes in the phase signal from an
-- arctan module, calculates the derivative, put it
-- through a window averager, and decides whether
-- to add it to the LO according to user commands.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity scalo_state_machine is
    generic(
        io_buf : buf_type := buf_for_io
    );
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        core_param_in   :   in  std_logic_vector(63 downto 0);
        -- data flow ports
        phase_in        :   in  std_logic_vector(15 downto 0);
        phase_out       :   out std_logic_vector(15 downto 0);
        -- control ports
        pid_reset_out   :   out std_logic
    );
end entity scalo_state_machine;

architecture behavioural of scalo_state_machine is
    signal phase_in_buf     :   signed(15 downto 0);
    signal phase_out_buf    :   signed(15 downto 0);

    type state_type is (s_IDLE, s_LOCKING);
    signal state            :   state_type := s_IDLE;

    signal phase_in_buf_1   :   signed(15 downto 0);
    signal phase_diff       :   signed(15 downto 0);
    type phase_diff_buf_type is array(0 to 255) of signed(15 downto 0);
    signal phase_diff_buf        :   phase_diff_buf_type := (others => (others => '0'));

    signal sum              :   signed(23 downto 0);
    signal bias             :   signed(15 downto 0);

    signal lock         :   std_logic := '0';
    signal clear        :   std_logic := '0';
    signal lock_1       :   std_logic := '0';
    signal clear_1      :   std_logic := '0';
    signal lock_rising  :   std_logic := '0';
    signal clear_rising :   std_logic := '0';
    signal lock_falling :   std_logic := '0';
begin
    use_input_buffer : if io_buf = buf_for_io or io_buf = buf_i_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    phase_in_buf <= (others => '0');
                else
                    phase_in_buf <= signed(phase_in);
                end if;
            end if;
        end process;
    end generate;

    no_input_buffer : if io_buf = buf_o_only or io_buf = buf_none generate
        phase_in_buf <= (others => '0') when rst = '1' else signed(phase_in);
    end generate;

    use_output_buffer : if io_buf = buf_for_io or io_buf = buf_o_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    phase_out <= (others => '0');
                else
                    phase_out <= std_logic_vector(phase_out_buf);
                end if;
            end if;
        end process;
    end generate;

    no_output_buffer : if io_buf = buf_i_only or io_buf = buf_none generate
        phase_out <= (others => '0') when rst = '1' else std_logic_vector(phase_out_buf);
    end generate;

    lock <= core_param_in(0); -- Address 0x00
    clear <= core_param_in(32); -- Address 0x01

    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                state <= s_IDLE;
            else
                case state is
                    when s_IDLE =>
                        if lock_rising = '1' then
                            state <= s_LOCKING;
                        end if;
                    when s_LOCKING =>
                        if lock_falling = '1' then
                            state <= s_IDLE;
                        end if;
                end case;
            end if;
        end if;
    end process;

    process(clk)
    begin
        if rising_edge(clk) then
            lock_1 <= lock;
            clear_1 <= clear;
        end if;
    end process;
    lock_rising <= '1' when lock = '1' and lock_1 = '0' else '0';
    clear_rising <= '1' when clear = '1' and clear_1 = '0' else '0';
    lock_falling <= '1' when lock = '0' and lock_1 = '1' else '0';

    buf_gen : for i in 0 to 254 generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    phase_diff_buf(i + 1) <= (others => '0');
                else
                    phase_diff_buf(i + 1) <= phase_diff_buf(i);
                end if;
            end if;
        end process;
    end generate;
    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                phase_in_buf_1 <= (others => '0');
                phase_diff <= (others => '0');
                phase_diff_buf(0) <= (others => '0');
                sum <= (others => '0');
            else
                phase_in_buf_1 <= phase_in_buf;
                phase_diff <= phase_in_buf_1 - phase_in_buf; -- positive diff indicates LO freq larger than sig so requires a negative bias
                phase_diff_buf(0) <= phase_diff;
                sum <= sum - ((7 downto 0 => phase_diff_buf(255)(15)) & phase_diff_buf(255)) + ((7 downto 0 => phase_diff_buf(0)(15)) & phase_diff_buf(0));
            end if;
        end if;
    end process;

    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                bias <= (others => '0');
            else
                if clear_rising = '1' then
                    bias <= (others => '0');
                elsif lock_rising = '1' then
                    bias <= bias + sum(23 downto 8);
                end if;
            end if;
        end if;
    end process;

    phase_out_buf <= bias;
    pid_reset_out <= '1' when state = s_IDLE else '0';
end architecture behavioural;






