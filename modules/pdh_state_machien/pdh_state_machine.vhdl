library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity pdh_state_machine is
    generic(
        io_buf : buf_type := buf_for_io
    );
    port (
        clk             : in  std_logic;  -- System clock
        rst             : in  std_logic;  -- System reset
        core_param_in   : in  std_logic_vector(127 downto 0); -- Standard parameter bus

        -- Data flow ports (to/from signal_router)
        sig_in          : in  std_logic_vector(15 downto 0);  -- Input signal for validity check
        pid_enable      : out std_logic;  -- Enable PID controller
        mixer_enable    : out std_logic;  -- Enable mixer
        sawtooth_enable : out std_logic;  -- Sawtooth wave for scanning
    );
end entity pdh_state_machine;

architecture behavioral of pdh_state_machine is
    -- Internal signals to unpack parameters from core_param_in
    signal pc_cmd                   : std_logic_vector(1 downto 0);
    signal threshold_signal_locking : signed(15 downto 0);
    signal threshold_signal_scanning: signed(15 downto 0);
    signal time_duration_scanning   : unsigned(31 downto 0);
    signal time_duration_locking    : unsigned(31 downto 0);

    -- State machine signals
    type state_type is (IDLE, SCANNING, LOCKING);
    signal current_state            : state_type;
    signal time_able                : unsigned(31 downto 0) := (others => '0');
    signal pc_cmd_prev              : std_logic_vector(1 downto 0) := "00";

    -- Internal buffer for input
    signal sig_in_buf               : signed(15 downto 0);

begin
    -- Unpack parameters from the core_param_in bus
    pc_cmd                      <= core_param_in(1 downto 0);
    threshold_signal_locking    <= signed(core_param_in(47 downto 32));
    threshold_signal_scanning   <= signed(core_param_in(79 downto 64));

    time_duration_scanning      <= unsigned(core_param_in(127 downto 96));
    time_duration_locking       <= unsigned(core_param_in(159 downto 128));

    -- Optional input buffer (following project standard)
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

    -- Main state machine process
    state_transition: process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                current_state <= IDLE;
                time_able <= (others => '0');
                pid_enable <= '0';
                mixer_enable <= '0';
                sawtooth_enable <= '0';
                pc_cmd_prev <= "00";
            else
                pc_cmd_prev <= pc_cmd;

                -- State transition logic
                case current_state is
                    when IDLE =>
                        pid_enable <= '0';
                        mixer_enable <= '0';
                        sawtooth_enable <= '0';
                        if pc_cmd = "01" and pc_cmd_prev = "00" then  -- Start command edge detection
                            current_state <= SCANNING;
                            time_able <= (others => '0');
                        end if;

                    when SCANNING =>
                        mixer_enable <= '1';
                        pid_enable <= '0';
                        sawtooth_enable <= '1';
                        if sig_in_buf < threshold_signal_scanning then
                            if time_able < time_duration_scanning then
                                time_able <= time_able + 1;
                            else
                                current_state <= LOCKING;
                                time_able <= (others => '0');
                            end if;
                        else
                            time_able <= (others => '0');
                        end if;
                        -- Stop command overrides everything
                        if pc_cmd = "00" and pc_cmd_prev = "01" then
                            current_state <= IDLE;
                        end if;

                    when LOCKING =>
                        mixer_enable    <= '1';
                        pid_enable      <= '1';
                        sawtooth_enable <= '0';
                        -- Stop command forces return to IDLE
                        if pc_cmd = "00" and pc_cmd_prev = "01" then
                            current_state <= IDLE;
                            time_able <= (others => '0');
                        -- Check for unlock condition
                        elsif sig_in_buf > threshold_signal_locking then
                            if time_able < time_duration_locking then
                                time_able <= time_able + 1;
                            else
                                current_state <= IDLE;
                                time_able <= (others => '0');
                            end if;
                        else
                            time_able <= (others => '0');
                        end if;
                end case;
            end if;
        end if;
    end process;

end architecture behavioral;