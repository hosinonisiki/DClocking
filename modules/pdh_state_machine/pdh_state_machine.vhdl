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
        core_param_in   : in  std_logic_vector(255 downto 0); -- Standard parameter bus

        -- Data flow ports (to/from signal_router)
        sig_in          : in  std_logic_vector(15 downto 0);  -- Input signal for validity check
        pid_enable      : out std_logic;  -- Enable PID controller
        mixer_enable    : out std_logic;  -- Enable mixer
        sawtooth_enable : out std_logic;  -- Sawtooth wave for scanning
        saw_input       : in  std_logic_vector(15 downto 0)
    );
end entity pdh_state_machine;

architecture behavioral of pdh_state_machine is
    -- Internal signals to unpack parameters from core_param_in
    signal pc_cmd                   : std_logic_vector(1 downto 0);
    signal threshold_signal_locking : signed(15 downto 0);
    signal threshold_signal_scanning: signed(15 downto 0);
    signal time_duration_scanning   : unsigned(31 downto 0);
    signal time_duration_locking    : unsigned(31 downto 0);
    signal auto_threshold_signal_scanning : signed(15 downto 0);
    signal auto_threshold_signal_locking  : signed(15 downto 0);
    signal auto_threshold_signal_scanning_buf : signed(15 downto 0);
    signal auto_threshold_signal_locking_buf : signed(15 downto 0);
    signal auto_time_duration_scanning      : unsigned(31 downto 0);
    signal auto_time_duration_locking      : unsigned(31 downto 0);
    signal max_sig_in                : signed(15 downto 0) := (15 => '1', others => '0');
    signal min_sig_in                : signed(15 downto 0) := (15 => '0', others => '1');
    signal diff_sig_in               : signed(16 downto 0); 
    signal diff_sig_in_buf           : signed(16 downto 0);
    signal scaled_lock_sig_in             : signed(32 downto 0);
    signal scaled_scan_sig_in             : signed(32 downto 0);
    signal scaled_lock_sig_in_buf    : signed(32 downto 0);
    signal scaled_scan_sig_in_buf    : signed(32 downto 0);
    signal coef_scan                  : signed(15 downto 0); 
    signal coef_lock                  : signed(15 downto 0);
    constant min_AUTO_TIME            : unsigned(15 downto 0) := to_unsigned(500, 16);

    -- State machine signals
    type state_type is (IDLE, AUTO_AMP, AUTO_TIME, AUTO_WAIT,AUTO_SCANNING, SCANNING, AUTO_LOCKING, LOCKING);
    signal current_state            : state_type;
    signal time_able                : unsigned(31 downto 0) := (others => '0');
    signal pc_cmd_prev              : std_logic_vector(1 downto 0) := "00";

    -- Internal buffer for input
    signal sig_in_buf               : signed(15 downto 0);

    -- Sawtooth jump detection signals
    signal saw_input_signed         : signed(15 downto 0);
    signal saw_input_prev           : signed(15 downto 0) := (others => '0');
    signal sawtooth_jump            : std_logic;
    
    -- Measurement done signal
    signal measurement_done         : std_logic;


begin
    -- Unpack parameters from the core_param_in bus
    pc_cmd                      <= core_param_in(1 downto 0); -- address 0x00
    threshold_signal_locking    <= signed(core_param_in(47 downto 32)); -- address 0x01
    threshold_signal_scanning   <= signed(core_param_in(79 downto 64)); -- address 0x02

    time_duration_scanning      <= unsigned(core_param_in(127 downto 96)); -- address 0x03
    time_duration_locking       <= unsigned(core_param_in(159 downto 128)); -- address 0x04

    coef_scan                   <= signed(core_param_in(175 downto 160)); -- address 0x05(-32768 to 32767) Q1.15
    coef_lock                   <= signed(core_param_in(207 downto 192)); -- address 0x06

    saw_input_signed          <= signed(saw_input); 

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

    diff_sig_in_buf <= resize(max_sig_in, 17) - resize(min_sig_in, 17); -- Q17.0
    process(clk)
    begin
        if rising_edge(clk) then
            diff_sig_in <= diff_sig_in_buf;
        end if;
    end process;

    scaled_scan_sig_in_buf <= diff_sig_in * coef_scan ;-- Q18.15
    scaled_lock_sig_in_buf <= diff_sig_in * coef_lock;-- Q18.15
    process(clk)
    begin
        if rising_edge(clk) then
            scaled_scan_sig_in <= scaled_scan_sig_in_buf;
            scaled_lock_sig_in <= scaled_lock_sig_in_buf;
        end if;
    end process;

    auto_threshold_signal_scanning_buf <= min_sig_in + scaled_scan_sig_in(30 downto 15); -- Q16.0
    auto_threshold_signal_locking_buf <= min_sig_in + scaled_lock_sig_in(30 downto 15);

    process(clk)
    begin
        if rising_edge(clk) then
            auto_threshold_signal_scanning <= auto_threshold_signal_scanning_buf;
            auto_threshold_signal_locking <= auto_threshold_signal_locking_buf;
        end if;
    end process;
    
    -- Main state machine process
    state_transition: process(clk)
    begin
        if rising_edge(clk) then
            if ((saw_input_signed(15) XOR saw_input_signed (14))='1' and saw_input_signed (15) /= saw_input_prev(15)) then
                sawtooth_jump <= '1';
            else
                sawtooth_jump <= '0';
            end if;

            saw_input_prev <= saw_input_signed;

            if rst = '1'  then
                current_state <= IDLE;
                time_able <= (others => '0');
                pid_enable <= '1';
                mixer_enable <= '1';
                sawtooth_enable <= '1';
                min_sig_in <= (15 => '0', others => '1');
                max_sig_in <= (15 => '1', others => '0');
                measurement_done <= '0';
                auto_time_duration_scanning <= (others => '0');
                auto_time_duration_locking <= (others => '0');
                pc_cmd_prev <= pc_cmd ; 
            else
                pc_cmd_prev <= pc_cmd;

                -- State transition logic
                case current_state is
                    when IDLE =>
                        pid_enable <= '1';
                        mixer_enable <= '1';
                        sawtooth_enable <= '1';
                        if pc_cmd = "01" and pc_cmd_prev = "00" then
                            current_state <= SCANNING;
                            time_able <= (others => '0');
                        elsif pc_cmd = "10" and pc_cmd_prev = "00" then
                            current_state <= AUTO_WAIT;
                        end if;

                    when AUTO_WAIT =>
                        pid_enable <= '1';
                        mixer_enable <= '1';
                        sawtooth_enable <= '0';
                        if pc_cmd = "00"  then 
                            current_state <= IDLE;
                        elsif sawtooth_jump = '1' then
                            current_state <= AUTO_AMP;
                            min_sig_in <= (15 => '0', others => '1');
                            max_sig_in <= (15 => '1', others => '0');
                        end if;

                    when AUTO_AMP =>
                        pid_enable <= '1';
                        mixer_enable <= '0'; 
                        sawtooth_enable <= '0';
                        
                        if sig_in_buf < min_sig_in then
                            min_sig_in <= sig_in_buf;
                        end if;
                        if sig_in_buf > max_sig_in then
                            max_sig_in <= sig_in_buf;
                        end if;
                        
                        if pc_cmd = "00" and pc_cmd_prev = "10" then
                            current_state <= IDLE;
                        elsif sawtooth_jump = '1' then
                            current_state <= AUTO_TIME;
                            time_able <= (others => '0');
                            measurement_done <= '0'; 
                        end if;

                    
                    when AUTO_TIME =>
                        pid_enable <= '1';
                        mixer_enable <= '0';
                        sawtooth_enable <= '0';

                        if measurement_done = '0' then
                            if sig_in_buf < auto_threshold_signal_scanning then
                                time_able <= time_able + 1;
                            else
                                if time_able > min_AUTO_TIME then
                                    measurement_done <= '1'; 
                                    auto_time_duration_scanning <= '0' & time_able(31 downto 1);--*0.5
                                    auto_time_duration_locking <= time_able(29 downto 0) & "00"; --*4
                                    time_able <= (others => '0');
                                else 
                                    time_able <= (others => '0');
                                end if;
                            end if;
                        end if;

                        if pc_cmd = "00" then
                            current_state <= IDLE;
                        elsif sawtooth_jump = '1' and auto_time_duration_scanning > 0 then
                            current_state <= AUTO_SCANNING;
                            time_able <= (others => '0');
                        end if;
                    
                    when AUTO_SCANNING => 
                        mixer_enable <= '0';
                        pid_enable <= '1';
                        sawtooth_enable <= '0';
                        if sig_in_buf < auto_threshold_signal_scanning then
                            if time_able < auto_time_duration_scanning then
                                time_able <= time_able + 1;
                            else
                                current_state <= AUTO_LOCKING;
                                time_able <= (others => '0');
                            end if;
                        else
                            time_able <= (others => '0');
                        end if;
                        if pc_cmd = "00" and pc_cmd_prev = "10" then
                            current_state <= IDLE;
                        end if;

                    when AUTO_LOCKING =>
                        mixer_enable    <= '0';
                        pid_enable      <= '0';
                        sawtooth_enable <= '1';
                        if pc_cmd = "00" and pc_cmd_prev = "10" then
                            current_state <= IDLE;
                            time_able <= (others => '0');
                        elsif sig_in_buf > auto_threshold_signal_locking then
                            if time_able < auto_time_duration_locking then
                                time_able <= time_able + 1;
                            elsif pc_cmd = "11" then
                                current_state <= IDLE;
                                time_able <= (others => '0');
                            end if;
                        else
                            time_able <= (others => '0');
                        end if;

                    --################ MANUAL MODE ################--
                    when SCANNING =>
                        mixer_enable <= '0';
                        pid_enable <= '1';
                        sawtooth_enable <= '0';
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
                        if pc_cmd = "00" and pc_cmd_prev = "01" then
                            current_state <= IDLE;
                        end if;

                    when LOCKING =>
                        mixer_enable    <= '0';
                        pid_enable      <= '0';
                        sawtooth_enable <= '1';
                        if pc_cmd = "00" and pc_cmd_prev = "01" then
                            current_state <= IDLE;
                            time_able <= (others => '0');
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