fres = 417800;
wres = fres*2*pi;
Q = 2800;

a = 1;
b = wres/Q;
c = wres^2;

wosc = c- 0.5*b^2;

k = 10;
mu = 100;

tspan = [0, 0.01];
x0 = [0.00000001; 0.1];

odefun = @(t, x) [x(2); 
                  (-c/a*x(1) -(b)/a.*x(2) -k*sin(wosc.*t) )];

[t, x] = ode45(odefun, tspan, x0);
figure(1);
plot(t, x(:,1), 'r-', 'LineWidth', 1.5);
hold on
grid on
figure(2);
plot(t, x(:,2), 'b-', 'LineWidth', 1.5);
grid on

dt = t(80001) - t(80000);     % Time step
Fs = 1 / dt;          % Sampling frequency in Hz

xf = x(80000:end, 2);

Y = fft(xf);
L = length(xf);        % Length of signal

% 4. Compute two-sided spectrum, then single-sided (P1) spectrum
P2 = abs(Y/L);
P1 = P2(1:L/2+1);
P1(2:end-1) = 2*P1(2:end-1);

% 5. Define the frequency domain vector (f)
f = Fs*(0:(L/2))/L;

% 6. Plot single-sided amplitude spectrum
figure(3);
plot(f, P1, 'LineWidth', 1.5);
title('Single-Sided Amplitude Spectrum of Oscope Signal');
xlabel('Frequency (Hz)');
ylabel('|P1(f)|');
grid on;