%% Script in cui ho messo le distorsioni misurate con FFT tramite l'altro script

% x = [100 150 200 300 400 500 600 700 800 900 1000];
% p1 = [3.351 4.888 5.603 9.249 11.04 13.17 13.97 14.37 14.77 15.31 16.17];
% p2 = [0.101 0.197 0.288 0.611 0.843 1.145 1.273 1.349 1.441 1.538 1.686];

% x = [100 150 200 300 400 500 600 700 800];
% p1 = [3.351 4.888 5.603 9.249 11.04 13.17 13.97 14.37 14.77];
% p2 = [0.101 0.197 0.288 0.611 0.843 1.145 1.273 1.349 1.441];

x = [20 40 60 80 100 120 140 160 180 200 300 400 500 600 700 800];
p1 = [1.406 2.556 3.606 4.578 5.522 5.635 6.284 7.465 7.934 8.408 15.36 18.87 21.00 21.53 22.85 25.86];
p2 = [0.030 0.031 0.056 0.085 0.125 0.130 0.167 0.195 0.240 0.262 0.649 1.167 1.686 1.858 2.088 2.625];

figure(1);
plot(x, p1, 'bo');
hold on
grid on
plot(x, p2, 'ro');
xlabel('Ampiezza Vac [mVpp]');
ylabel('Modulo componente in frequenza [mV]');


figure(2);
plot(x, p2./p1, 'bo');
hold on
grid on
xlabel('Ampiezza Vac [mVpp]');
ylabel('Distorsione secondo modo [mV/mV]');

poly1 = polyfit(x, p1, 2);
poly2 = polyfit(x, p2, 2);
polyd = polyfit(x, p2./p1, 2);

x = linspace(0, 800, 10000);

fit1 = poly1(1).*x.*x + poly1(2).*x + poly1(3);
fit2 = poly2(1).*x.*x + poly2(2).*x + poly2(3);
fitd = polyd(1).*x.*x + polyd(2).*x + polyd(3);

figure(1);
plot(x, fit1, 'b');
plot(x, fit2, 'r');
legend('Primo modo', 'Secondo modo')

linear1 = poly1(2).*x + poly1(3);
linear2 = poly2(2).*x + poly2(3);
lineard = polyd(2).*x + polyd(3);
plot(x, linear1, 'k--','HandleVisibility','off');
plot(x, linear2, 'k--','HandleVisibility','off');


figure(2);
plot(x, fitd, 'b');
plot(x, lineard, 'k--');
