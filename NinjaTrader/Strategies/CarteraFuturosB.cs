// CarteraFuturosB.cs — NinjaTrader 8 (NinjaScript). Cartera de futuros (modo B, o modo A para firmas con cierre 16:45).
// Reglas tomadas de research/CARTERA_FUTUROS.md y de los preregistros/resultados citados en cada estrategia. Horas en Nueva York.
//
// Diseño:
// - Una sola estrategia con varias series de 1 minuto (una por mercado). Cada sub-estrategia decide una posición con signo por
//   mercado; el bot suma las posiciones de todas y envía al mercado solo la diferencia (posición neta), porque varias estrategias
//   pueden estar a la vez, incluso en sentido contrario, en el mismo futuro.
// - Stops y objetivos se vigilan dentro del bot (no hay órdenes stop en el servidor): el PC/VPS tiene que estar encendido y conectado.
// - Tamaño: riesgo% del capital / sigma de la propia franja (como el EA de MT5), con peso 0,2 en las estrategias diarias y control de
//   volatilidad de la cartera (escala = volatilidad objetivo / volatilidad de los últimos 60 días, limitada a 0,5-2).
// - Por defecto solo opera en cuentas de simulación (Sim101, Playback...). Ver README_NINJATRADER.md.
#region Using declarations
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Globalization;
using System.IO;
using System.Linq;
using NinjaTrader.Cbi;
using NinjaTrader.Data;
using NinjaTrader.NinjaScript;
#endregion

namespace NinjaTrader.NinjaScript.Strategies
{
    public enum ModoCarteraFuturos { A_cierre_1645, B_completa }

    public class CarteraFuturosB : Strategy
    {
        // ---------- tipos internos ----------
        private class Ventana        // estrategia de franja horaria fija
        {
            public string Nombre; public int Mercado; public int Tipo; public int HIni; public int HFin; public int Lado;
            public int Noches; public double Peso; public bool Activa;
        }
        private class Ruptura        // estrategia diaria de ruptura (C93 día anterior / C99-C102 rango asiático)
        {
            public string Nombre; public int Mercado; public bool Asiatica; public bool Activa;
            public DateTime Dia = DateTime.MinValue; public double H, L, Atr; public bool Hecha, Lista;
        }
        private class Pos            // posición virtual de una sub-estrategia
        {
            public string Estrategia; public int Mercado; public int Contratos; public double Entrada; public double Stop; public double Objetivo;
            public DateTime SalidaNY; public double Sigma; public DateTime EntradaNY;
        }

        // índices de mercado (orden de AddDataSeries + 1; el 0 es el instrumento del gráfico, no se usa para operar)
        private const int ORO = 1, PLATA = 2, COBRE = 3, NIKKEI = 4, YEN = 5, BITCOIN = 6, CESTA0 = 7;   // CESTA0..CESTA0+11: E12
        private string[] nombres;
        private TimeZoneInfo tzNY, tzNT;
        private readonly List<Ventana> ventanas = new List<Ventana>();
        private readonly List<Ruptura> rupturas = new List<Ruptura>();
        private readonly List<Pos> posiciones = new List<Pos>();
        private readonly Dictionary<string, DateTime> hechoHoy = new Dictionary<string, DateTime>();
        private bool[] pendiente;
        private SessionIterator[] sesiones;
        private HashSet<DateTime> festivos = new HashSet<DateTime>();
        private DateTime diaActualNY = DateTime.MinValue, ultimoCierreDiario = DateTime.MinValue;
        private double pnlInicioDia = double.NaN; private bool paradoHoy;
        private double escalaVol = 1.0;
        private string archivoLog, archivoPnl;

        // ---------- parámetros ----------
        [NinjaScriptProperty][Display(Name = "Modo", Order = 1, GroupName = "1. General")]
        public ModoCarteraFuturos Modo { get; set; }
        [NinjaScriptProperty][Range(0.01, 5)][Display(Name = "Riesgo por operación (% del capital)", Order = 2, GroupName = "1. General")]
        public double RiesgoPct { get; set; }
        [NinjaScriptProperty][Range(0, 1)][Display(Name = "Peso de las estrategias diarias (C93, C99, C101, C102, bitcoin)", Order = 3, GroupName = "1. General")]
        public double PesoDiarias { get; set; }
        [NinjaScriptProperty][Display(Name = "Control de volatilidad de la cartera", Order = 4, GroupName = "1. General")]
        public bool ControlVolatilidad { get; set; }
        [NinjaScriptProperty][Range(0, 100000000)][Display(Name = "Capital (USD; 0 = saldo de la cuenta)", Order = 5, GroupName = "1. General")]
        public double CapitalUSD { get; set; }
        [NinjaScriptProperty][Range(0, 1)][Display(Name = "Fracción mínima para redondear a 1 contrato", Order = 6, GroupName = "1. General")]
        public double RedondeoMin { get; set; }
        [NinjaScriptProperty][Display(Name = "Solo cuentas de simulación", Order = 7, GroupName = "1. General")]
        public bool SoloSimulacion { get; set; }
        [NinjaScriptProperty][Display(Name = "Operar también en el histórico (Strategy Analyzer)", Order = 8, GroupName = "1. General")]
        public bool PermitirHistorico { get; set; }

        [NinjaScriptProperty][Range(0, 50)][Display(Name = "Pérdida diaria máxima (% del capital; 0 = sin límite)", Order = 1, GroupName = "2. Protecciones")]
        public double PerdidaDiariaMaxPct { get; set; }
        [NinjaScriptProperty][Range(1, 20)][Display(Name = "Stop de catástrofe de las franjas (sigmas)", Order = 2, GroupName = "2. Protecciones")]
        public double StopSigmas { get; set; }
        [NinjaScriptProperty][Range(1, 50)][Display(Name = "Exposición máxima por operación (× capital)", Order = 3, GroupName = "2. Protecciones")]
        public double TopeExposicion { get; set; }

        [NinjaScriptProperty][Display(Name = "Oro (p. ej. MGC 12-26)", Order = 1, GroupName = "3. Contratos (cambiar al vencimiento)")]
        public string InstOro { get; set; }
        [NinjaScriptProperty][Display(Name = "Plata (p. ej. SIL 12-26)", Order = 2, GroupName = "3. Contratos (cambiar al vencimiento)")]
        public string InstPlata { get; set; }
        [NinjaScriptProperty][Display(Name = "Cobre (p. ej. MHG 12-26)", Order = 3, GroupName = "3. Contratos (cambiar al vencimiento)")]
        public string InstCobre { get; set; }
        [NinjaScriptProperty][Display(Name = "Nikkei USD (p. ej. NKD 12-26)", Order = 4, GroupName = "3. Contratos (cambiar al vencimiento)")]
        public string InstNikkei { get; set; }
        [NinjaScriptProperty][Display(Name = "Yen (p. ej. MJY 12-26 o 6J 12-26)", Order = 5, GroupName = "3. Contratos (cambiar al vencimiento)")]
        public string InstYen { get; set; }
        [NinjaScriptProperty][Display(Name = "Bitcoin micro (p. ej. MBT 11-26)", Order = 6, GroupName = "3. Contratos (cambiar al vencimiento)")]
        public string InstBitcoin { get; set; }
        [NinjaScriptProperty][Display(Name = "Cesta E12 (12 contratos separados por comas: CL HO RB NG ZC ZS ZW ZL ZM KE LE HE)", Order = 7, GroupName = "3. Contratos (cambiar al vencimiento)")]
        public string InstCesta { get; set; }

        [NinjaScriptProperty][Display(Name = "Festivos NYSE (AAAA-MM-DD, separados por comas; ampliar cada año)", Order = 1, GroupName = "4. Calendario")]
        public string FestivosNYSE { get; set; }

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Description = "Cartera de futuros (C93, C99, C101, C102, E8, E9, E10, E11, E12, E13, E15, E16, plata viernes, bitcoin 21-23 UTC). Ver README_NINJATRADER.md.";
                Name = "CarteraFuturosB";
                Calculate = Calculate.OnPriceChange;
                IsUnmanaged = true;
                IsExitOnSessionCloseStrategy = false;
                BarsRequiredToTrade = 0;
                MaximumBarsLookBack = MaximumBarsLookBack.Infinite;
                StartBehavior = StartBehavior.ImmediatelySubmit;
                RealtimeErrorHandling = RealtimeErrorHandling.StopCancelClose;
                TraceOrders = false;
                Modo = ModoCarteraFuturos.B_completa;
                RiesgoPct = 0.5; PesoDiarias = 0.2; ControlVolatilidad = true; CapitalUSD = 0; RedondeoMin = 0.5;
                SoloSimulacion = true; PermitirHistorico = false;
                PerdidaDiariaMaxPct = 3.0; StopSigmas = 4.0; TopeExposicion = 6.0;
                InstOro = "MGC 12-26"; InstPlata = "SIL 12-26"; InstCobre = "MHG 12-26"; InstNikkei = "NKD 12-26"; InstYen = "MJY 12-26"; InstBitcoin = "MBT 11-26";
                InstCesta = "MCL 12-26,HO 12-26,RB 12-26,QG 12-26,ZC 12-26,ZS 01-27,ZW 12-26,ZL 12-26,ZM 12-26,KE 12-26,LE 12-26,HE 12-26";
                FestivosNYSE = "2026-01-01,2026-01-19,2026-02-16,2026-04-03,2026-05-25,2026-06-19,2026-07-03,2026-09-07,2026-11-26,2026-12-25," +
                               "2027-01-01,2027-01-18,2027-02-15,2027-03-26,2027-05-31,2027-06-18,2027-07-05,2027-09-06,2027-11-25,2027-12-24";
            }
            else if (State == State.Configure)
            {
                var lista = new List<string> { InstOro, InstPlata, InstCobre, InstNikkei, InstYen, InstBitcoin };
                lista.AddRange(InstCesta.Split(',').Select(s => s.Trim()).Where(s => s.Length > 0));
                nombres = new string[lista.Count + 1];
                nombres[0] = "grafico";
                for (int i = 0; i < lista.Count; i++) { AddDataSeries(lista[i], BarsPeriodType.Minute, 1); nombres[i + 1] = lista[i]; }
            }
            else if (State == State.DataLoaded)
            {
                tzNY = TimeZoneInfo.FindSystemTimeZoneById("Eastern Standard Time");
                tzNT = Core.Globals.GeneralOptions.TimeZoneInfo;
                pendiente = new bool[BarsArray.Length];
                sesiones = new SessionIterator[BarsArray.Length];
                for (int i = 0; i < BarsArray.Length; i++) sesiones[i] = new SessionIterator(BarsArray[i]);
                foreach (string f in FestivosNYSE.Split(','))
                {
                    DateTime d;
                    if (DateTime.TryParseExact(f.Trim(), "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out d)) festivos.Add(d.Date);
                }
                string dir = Path.Combine(Core.Globals.UserDataDir, "CarteraFuturos");
                Directory.CreateDirectory(dir);
                archivoLog = Path.Combine(dir, "CarteraFuturos_log.csv");
                archivoPnl = Path.Combine(dir, "CarteraFuturos_pnl_diario.csv");
                Configurar();
            }
        }

        // ================= definición de las estrategias =================
        // Tipo de día: 1 viernes, 2 víspera de festivo NYSE, 3 D-2 (quedan 2 laborables en el mes), 4 Q0 (último laborable del trimestre),
        // 5 día antes de la víspera (1 noche), 6 Q+2 (2.º laborable de ene/abr/jul/oct), 8 Q-2 (penúltimo laborable de mar/jun/sep/dic),
        // 9 bitcoin (todos los laborables, horas UTC).
        private void Configurar()
        {
            bool b = Modo == ModoCarteraFuturos.B_completa;
            int salidaViernes = b ? 1655 : 1645;
            // E8 oro viernes (C45/E8b): largo 16:00 → 16:55 (B) / 16:45 (A)
            ventanas.Add(new Ventana { Nombre = "E8_oro_viernes", Mercado = ORO, Tipo = 1, HIni = 1600, HFin = salidaViernes, Lado = 1, Peso = 1, Activa = true });
            // E10 plata víspera de festivo (E10/E10b): largo 16:00 → 16:55 (B) / 16:45 (A)
            ventanas.Add(new Ventana { Nombre = "E10_plata_vispera", Mercado = PLATA, Tipo = 2, HIni = 1600, HFin = salidaViernes, Lado = 1, Peso = 1, Activa = true });
            // plata viernes 16:30 → 17:00 (solo B; sale a las 16:59 por la pausa del CME)
            ventanas.Add(new Ventana { Nombre = "plata_viernes", Mercado = PLATA, Tipo = 1, HIni = 1630, HFin = 1659, Lado = 1, Peso = 1, Activa = b });
            // E9 yen fin de mes: USDJPY largo 07:00 → 08:00 el D-2  ⇒  futuro del yen (JPY/USD) CORTO
            ventanas.Add(new Ventana { Nombre = "E9_yen_fin_mes", Mercado = YEN, Tipo = 3, HIni = 700, HFin = 800, Lado = -1, Peso = 1, Activa = true });
            // E11 yen fin de trimestre: USDJPY corto 00:30 → 02:00 el Q0  ⇒  futuro del yen LARGO; 1/3 del riesgo (solo la pata USDJPY de la cesta)
            ventanas.Add(new Ventana { Nombre = "E11_yen_fin_trim", Mercado = YEN, Tipo = 4, HIni = 30, HFin = 200, Lado = 1, Peso = 1.0 / 3, Activa = true });
            // E13 Nikkei Q+2 largo 15:00 → 16:00; E16 Nikkei Q-2 corto 20:00 → 21:00; E15 oro D-2 corto 09:30 → 10:00
            ventanas.Add(new Ventana { Nombre = "E13_nikkei_Qmas2", Mercado = NIKKEI, Tipo = 6, HIni = 1500, HFin = 1600, Lado = 1, Peso = 1, Activa = true });
            ventanas.Add(new Ventana { Nombre = "E16_nikkei_Qmenos2", Mercado = NIKKEI, Tipo = 8, HIni = 2000, HFin = 2100, Lado = -1, Peso = 1, Activa = true });
            ventanas.Add(new Ventana { Nombre = "E15_oro_Dmenos2", Mercado = ORO, Tipo = 3, HIni = 930, HFin = 1000, Lado = -1, Peso = 1, Activa = true });
            // E12 materias primas víspera de festivo: largo 13:55 del día anterior a la víspera → 13:55 de la víspera (1 noche; solo B); 1/12 del riesgo por mercado
            for (int k = CESTA0; k < BarsArray.Length; k++)
                ventanas.Add(new Ventana { Nombre = "E12_cesta_" + nombres[k].Split(' ')[0], Mercado = k, Tipo = 5, HIni = 1355, HFin = 1355, Lado = 1, Noches = 1,
                                           Peso = 1.0 / Math.Max(1, BarsArray.Length - CESTA0), Activa = b });
            // bitcoin 21:00 → 23:00 UTC los laborables (C2; solo B); peso de estrategia diaria
            ventanas.Add(new Ventana { Nombre = "bitcoin_21_23_UTC", Mercado = BITCOIN, Tipo = 9, HIni = 2100, HFin = 2300, Lado = 1, Peso = PesoDiarias, Activa = b });

            rupturas.Add(new Ruptura { Nombre = "C93_oro_dia_anterior", Mercado = ORO, Asiatica = false, Activa = true });
            rupturas.Add(new Ruptura { Nombre = "C99_oro_rango_asia", Mercado = ORO, Asiatica = true, Activa = true });
            rupturas.Add(new Ruptura { Nombre = "C101_nikkei_rango_asia", Mercado = NIKKEI, Asiatica = true, Activa = true });
            rupturas.Add(new Ruptura { Nombre = "C102_cobre_rango_asia", Mercado = COBRE, Asiatica = true, Activa = true });
        }

        // ================= horas y calendario =================
        private DateTime ANY(DateTime tNT) { return TimeZoneInfo.ConvertTime(DateTime.SpecifyKind(tNT, DateTimeKind.Unspecified), tzNT, tzNY); }
        private DateTime DeNY(DateTime tNY) { return TimeZoneInfo.ConvertTime(DateTime.SpecifyKind(tNY, DateTimeKind.Unspecified), tzNY, tzNT); }
        private static DateTime Hora(DateTime dia, int hhmm) { return dia.Date.AddHours(hhmm / 100).AddMinutes(hhmm % 100); }
        private static int HM(DateTime t) { return t.Hour * 100 + t.Minute; }
        private static bool Laborable(DateTime d) { return d.DayOfWeek != DayOfWeek.Saturday && d.DayOfWeek != DayOfWeek.Sunday; }
        private bool Festivo(DateTime d) { return festivos.Contains(d.Date); }
        private DateTime HabilSiguiente(DateTime d) { DateTime s = d.Date.AddDays(1); while (!Laborable(s) || Festivo(s)) s = s.AddDays(1); return s; }
        private static DateTime SumarLaborables(DateTime d, int n) { DateTime s = d.Date; for (int k = 0; k < n; k++) { s = s.AddDays(1); while (!Laborable(s)) s = s.AddDays(1); } return s; }
        private static int LaborablesRestantesMes(DateTime d)
        {
            int n = 0; for (DateTime s = d.Date.AddDays(1); s.Month == d.Month; s = s.AddDays(1)) if (Laborable(s)) n++; return n;
        }
        private bool EsVispera(DateTime d) { return Laborable(d) && !Festivo(d) && Festivo(HabilSiguiente(d)); }
        private bool EsDiaAntesDeVispera(DateTime d) { DateTime s = HabilSiguiente(d); return Laborable(d) && !Festivo(d) && s == d.Date.AddDays(1) && EsVispera(s); }
        private static bool EsQmas2(DateTime d)
        {
            if (!Laborable(d) || d.Month % 3 != 1 || (d.Month == 1 && d.Day == 1)) return false;
            int n = 0;
            for (DateTime s = new DateTime(d.Year, d.Month, 1); s <= d.Date; s = s.AddDays(1)) if (Laborable(s) && !(s.Month == 1 && s.Day == 1)) n++;
            return n == 2;
        }
        private bool DiaValido(Ventana v, DateTime dNY)
        {
            switch (v.Tipo)
            {
                case 1: return dNY.DayOfWeek == DayOfWeek.Friday && !Festivo(dNY);
                case 2: return EsVispera(dNY);
                case 3: return Laborable(dNY) && LaborablesRestantesMes(dNY) == 2;
                case 4: return Laborable(dNY) && LaborablesRestantesMes(dNY) == 0 && dNY.Month % 3 == 0;
                case 5: return EsDiaAntesDeVispera(dNY);
                case 6: return EsQmas2(dNY);
                case 8: return Laborable(dNY) && dNY.Month % 3 == 0 && LaborablesRestantesMes(dNY) == 1;
                default: return false;
            }
        }

        // ================= precios del histórico =================
        // índice de la última barra de 1 min del mercado i que cierra en o antes de tNY (máx. 10 min de antigüedad); -1 si no hay
        private int IndiceEn(int i, DateTime tNY)
        {
            Bars b = BarsArray[i]; int n = b.Count; if (n == 0) return -1;
            DateTime t = DeNY(tNY);
            int lo = 0, hi = Math.Min(n - 1, CurrentBars[i]); if (hi < 0) return -1;
            if (b.GetTime(lo) > t) return -1;
            while (lo < hi) { int mid = (lo + hi + 1) / 2; if (b.GetTime(mid) <= t) lo = mid; else hi = mid - 1; }
            return (t - b.GetTime(lo)).TotalMinutes <= 10 ? lo : -1;
        }
        private double PrecioEn(int i, DateTime tNY) { int k = IndiceEn(i, tNY); return k < 0 ? 0 : BarsArray[i].GetClose(k); }

        // sigma de ln(P(fin)/P(ini)) en los últimos n laborables (fin = n.º de noches laborables después; horas NY, o UTC si utc = true)
        private double Sigma(int i, int hIni, int hFin, int noches, int n, DateTime hoyNY, bool utc = false)
        {
            var r = new List<double>();
            for (int k = 1; k <= 400 && r.Count < n; k++)
            {
                DateTime d = hoyNY.Date.AddDays(-k); if (!Laborable(d)) continue;
                DateTime t0, t1;
                if (utc) { t0 = UTCaNY(Hora(d, hIni)); t1 = UTCaNY(Hora(d, hFin)); }
                else { t0 = Hora(d, hIni); t1 = Hora(SumarLaborables(d, noches), hFin); }
                double p0 = PrecioEn(i, t0), p1 = PrecioEn(i, t1);
                if (p0 > 0 && p1 > 0) r.Add(Math.Log(p1 / p0));
            }
            if (r.Count < Math.Min(30, n * 2 / 3)) return 0;
            double m = r.Average(); return Math.Sqrt(r.Sum(x => (x - m) * (x - m)) / (r.Count - 1));
        }
        private DateTime UTCaNY(DateTime tUtc) { return TimeZoneInfo.ConvertTimeFromUtc(DateTime.SpecifyKind(tUtc, DateTimeKind.Utc), tzNY); }

        // ¿la sesión del mercado i sigue abierta (sin cierre largo, >2 h) hasta tNY? (vísperas con cierre anticipado, fines de semana)
        private bool SesionCubre(int i, DateTime ahoraNT, DateTime hastaNY)
        {
            try
            {
                sesiones[i].GetNextSession(ahoraNT, true);
                DateTime fin = sesiones[i].ActualSessionEnd;
                DateTime hasta = DeNY(hastaNY);
                while (fin < hasta)
                {
                    sesiones[i].GetNextSession(fin.AddMinutes(1), true);
                    if ((sesiones[i].ActualSessionBegin - fin).TotalHours > 2) return false;
                    fin = sesiones[i].ActualSessionEnd;
                }
                return true;
            }
            catch { return true; }
        }

        // ================= capital, tamaño y control de volatilidad =================
        private double Capital()
        {
            if (CapitalUSD > 0) return CapitalUSD;
            double c = Account != null ? Account.Get(AccountItem.CashValue, Currency.UsDollar) : 0;
            return c > 0 ? c : 50000;
        }
        private int Contratos(int i, double riesgoFrac, double sigma, double precio)
        {
            if (sigma <= 0 || precio <= 0) return 0;
            double pv = Instruments[i].MasterInstrument.PointValue;
            double nocional = Math.Min(riesgoFrac / sigma, TopeExposicion) * Capital() * escalaVol;
            double x = nocional / (precio * pv);
            int q = (int)Math.Floor(x); if (x - q >= RedondeoMin) q++;
            return q;
        }
        private double PnlTotal()
        {
            double p = SystemPerformance.AllTrades.TradesPerformance.Currency.CumProfit;
            for (int i = 1; i < BarsArray.Length; i++)
                if (Positions[i].MarketPosition != MarketPosition.Flat && CurrentBars[i] >= 0)
                    p += Positions[i].GetUnrealizedProfitLoss(PerformanceUnit.Currency, Closes[i][0]);
            return p;
        }
        private void ActualizarEscalaVol()
        {
            escalaVol = 1.0;
            if (!ControlVolatilidad || !File.Exists(archivoPnl)) return;
            var x = File.ReadAllLines(archivoPnl).Skip(1).Select(l => l.Split(',')).Where(c => c.Length >= 2)
                        .Select(c => double.Parse(c[1], CultureInfo.InvariantCulture)).ToList();
            if (x.Count < 40) return;
            var u = x.Skip(Math.Max(0, x.Count - 60)).ToList(); double m = u.Average();
            double sd = Math.Sqrt(u.Sum(v => (v - m) * (v - m)) / (u.Count - 1));
            // volatilidad diaria de la cartera a riesgo base 0,5 % en 2018-2026 (escenario_comp / puntos45): A 0,36 %, B 0,50 %
            double objetivo = (Modo == ModoCarteraFuturos.B_completa ? 0.50 : 0.36) * RiesgoPct / 0.5 / 100.0;
            if (sd > 0) escalaVol = Math.Max(0.5, Math.Min(2.0, objetivo / sd));
        }

        // ================= registro =================
        private void Registrar(DateTime ny, string estr, int i, string evento, int q, double sigma, double precio, double pnl)
        {
            try
            {
                bool nuevo = !File.Exists(archivoLog);
                using (var w = new StreamWriter(archivoLog, true))
                {
                    if (nuevo) w.WriteLine("hora_NY,estrategia,contrato,evento,contratos,sigma_pb,precio,pnl_estimado_usd,capital,escala_vol,modo");
                    w.WriteLine(string.Join(",", ny.ToString("yyyy-MM-dd HH:mm:ss"), estr, i > 0 ? nombres[i] : "", evento, q,
                        (sigma * 1e4).ToString("F2", CultureInfo.InvariantCulture), precio.ToString(CultureInfo.InvariantCulture),
                        pnl.ToString("F2", CultureInfo.InvariantCulture), Capital().ToString("F0", CultureInfo.InvariantCulture),
                        escalaVol.ToString("F2", CultureInfo.InvariantCulture), Modo));
                }
            }
            catch (Exception e) { Print("CarteraFuturosB: no se pudo escribir el registro: " + e.Message); }
            Print(string.Format("{0:yyyy-MM-dd HH:mm} NY | {1} | {2} | {3} | {4}", ny, estr, i > 0 ? nombres[i] : "", evento, q));
        }

        // ================= bucle principal =================
        protected override void OnBarUpdate()
        {
            if (BarsInProgress == 0 || CurrentBars[BarsInProgress] < 1) return;
            if (State == State.Historical && !PermitirHistorico) return;
            if (SoloSimulacion && State == State.Realtime && Account != null &&
                !(Account.Name.StartsWith("Sim", StringComparison.OrdinalIgnoreCase) || Account.Name.StartsWith("Playback", StringComparison.OrdinalIgnoreCase)))
            {
                if (!hechoHoy.ContainsKey("aviso_sim")) { hechoHoy["aviso_sim"] = DateTime.MaxValue; Print("CarteraFuturosB: la cuenta " + Account.Name + " no es de simulación y 'Solo cuentas de simulación' está activado: no opera."); }
                return;
            }
            int bip = BarsInProgress;
            // hora actual: el bar en formación lleva la marca de su cierre; la hora "real" es un minuto antes como mucho
            DateTime ahoraNT = State == State.Realtime ? Core.Globals.Now : Times[bip][0].AddMinutes(-1);
            DateTime ny = ANY(ahoraNT);
            NuevoDia(ny);
            Protecciones(ny);
            VigilarSalidas(bip, ny);
            if (!paradoHoy)
            {
                foreach (var v in ventanas) if (v.Activa) EntradaVentana(v, ny, ahoraNT);
                foreach (var r in rupturas) if (r.Activa) GestionarRuptura(r, bip, ny, ahoraNT);
            }
            Reconciliar(ny);
        }

        private void NuevoDia(DateTime ny)
        {
            // cierre diario a las 17:00 NY: guarda el resultado del día para el control de volatilidad
            DateTime corte = ny.Hour >= 17 ? ny.Date : ny.Date.AddDays(-1);
            if (corte != ultimoCierreDiario)
            {
                double p = PnlTotal();
                if (!double.IsNaN(pnlInicioDia) && Laborable(corte))
                {
                    try
                    {
                        bool nuevo = !File.Exists(archivoPnl);
                        using (var w = new StreamWriter(archivoPnl, true))
                        {
                            if (nuevo) w.WriteLine("dia,pnl_frac_capital");
                            w.WriteLine(corte.ToString("yyyy-MM-dd") + "," + ((p - pnlInicioDia) / Capital()).ToString("R", CultureInfo.InvariantCulture));
                        }
                    }
                    catch { }
                }
                pnlInicioDia = p; ultimoCierreDiario = corte; paradoHoy = false;
                ActualizarEscalaVol();
            }
            if (ny.Date != diaActualNY) diaActualNY = ny.Date;
        }

        private void Protecciones(DateTime ny)
        {
            if (PerdidaDiariaMaxPct <= 0 || paradoHoy || double.IsNaN(pnlInicioDia)) return;
            double dia = PnlTotal() - pnlInicioDia;
            if (dia <= -PerdidaDiariaMaxPct / 100.0 * Capital())
            {
                paradoHoy = true;
                foreach (var p in posiciones.ToList()) { Registrar(ny, p.Estrategia, p.Mercado, "cierre_perdida_diaria", p.Contratos, p.Sigma, Closes[p.Mercado][0], 0); posiciones.Remove(p); }
                Registrar(ny, "cartera", 0, "parada_hasta_las_17h_perdida_diaria_" + dia.ToString("F0"), 0, 0, 0, dia);
            }
        }

        private bool Hecho(string clave, DateTime dia) { DateTime d; return hechoHoy.TryGetValue(clave, out d) && d == dia.Date; }
        private void Marcar(string clave, DateTime dia) { hechoHoy[clave] = dia.Date; }

        // ---------- franjas horarias ----------
        private void EntradaVentana(Ventana v, DateTime ny, DateTime ahoraNT)
        {
            DateTime inicio, salida; DateTime dia;
            if (v.Tipo == 9)
            {
                DateTime utc = TimeZoneInfo.ConvertTimeToUtc(DateTime.SpecifyKind(ny, DateTimeKind.Unspecified), tzNY);
                dia = utc.Date; if (!Laborable(dia)) return;
                inicio = UTCaNY(Hora(dia, v.HIni)); salida = UTCaNY(Hora(dia, v.HFin));
            }
            else
            {
                dia = ny.Date; if (!DiaValido(v, dia)) return;
                inicio = Hora(dia, v.HIni); salida = v.Noches > 0 ? Hora(SumarLaborables(dia, v.Noches), v.HFin) : Hora(dia, v.HFin);
            }
            if (ny < inicio || ny >= inicio.AddMinutes(5) || Hecho(v.Nombre, dia)) return;
            Marcar(v.Nombre, dia);
            int i = v.Mercado;
            if (i >= BarsArray.Length || CurrentBars[i] < 1) { Registrar(ny, v.Nombre, i, "sin_datos", 0, 0, 0, 0); return; }
            if ((ahoraNT - Times[i][0]).TotalMinutes > 10) { Registrar(ny, v.Nombre, i, "sin_precio_reciente", 0, 0, 0, 0); return; }
            if (!SesionCubre(i, ahoraNT, salida)) { Registrar(ny, v.Nombre, i, "sin_entrada_cierre_de_sesion_antes_de_la_salida", 0, 0, Closes[i][0], 0); return; }
            double sg = v.Tipo == 9 ? Sigma(i, v.HIni, v.HFin, 0, 60, ny, true) : Sigma(i, v.HIni, v.HFin, v.Noches, 60, ny);
            if (sg <= 0) { Registrar(ny, v.Nombre, i, "sin_entrada_sigma_faltan_datos_historicos", 0, 0, Closes[i][0], 0); return; }
            double precio = Closes[i][0];
            int q = Contratos(i, RiesgoPct / 100.0 * v.Peso, sg, precio);
            if (q <= 0) { Registrar(ny, v.Nombre, i, "sin_entrada_0_contratos", 0, sg, precio, 0); return; }
            posiciones.Add(new Pos { Estrategia = v.Nombre, Mercado = i, Contratos = v.Lado * q, Entrada = precio,
                                     Stop = precio * (1 - v.Lado * StopSigmas * sg), Objetivo = double.NaN, SalidaNY = salida, Sigma = sg, EntradaNY = ny });
            Registrar(ny, v.Nombre, i, v.Lado > 0 ? "compra" : "venta", q, sg, precio, 0);
        }

        // ---------- rupturas diarias ----------
        // C93: máximo/mínimo de la sesión anterior (17:00→17:00 NY), ATR(14) de sesiones; ventana 08:00-15:00; stop 1 ATR, objetivo 3 ATR; salida 16:45.
        // C99/C101/C102: rango 19:00 (día anterior) → 03:00; ventana 03:00-11:00; stop = el otro extremo; objetivo = 1 × anchura; salida 16:45.
        private void GestionarRuptura(Ruptura r, int bip, DateTime ny, DateTime ahoraNT)
        {
            DateTime dia = ny.Date; if (!Laborable(dia)) return;
            int i = r.Mercado; if (i >= BarsArray.Length || CurrentBars[i] < 1) return;
            int hIni = r.Asiatica ? 300 : 800, hFin = r.Asiatica ? 1100 : 1500;
            if (r.Dia != dia) { r.Dia = dia; r.Hecha = false; r.Lista = false; }
            int hm = HM(ny);
            if (!r.Lista && hm >= hIni && hm < hFin)
            {
                r.Lista = true;
                if (!PrepararNiveles(r, dia)) { r.Hecha = true; Registrar(ny, r.Nombre, i, "sin_niveles_faltan_datos", 0, 0, 0, 0); return; }
                // si el bot arranca a mitad de la ventana y la ruptura ya ocurrió, no entra tarde (la regla es la PRIMERA ruptura)
                Bars bb = BarsArray[i]; DateTime desde = Hora(dia, hIni);
                for (int k = CurrentBars[i] - 1; k >= 0; k--)
                {
                    DateTime t = ANY(bb.GetTime(k)).AddMinutes(-1); if (t < desde) break;
                    if (bb.GetHigh(k) > r.H || bb.GetLow(k) < r.L) { r.Hecha = true; Registrar(ny, r.Nombre, i, "sin_entrada_ruptura_ya_ocurrida_al_arrancar", 0, 0, Closes[i][0], 0); return; }
                }
            }
            if (!r.Lista || r.Hecha || bip != i || hm < hIni || hm >= hFin) return;
            double hi = Highs[i][0], lo = Lows[i][0];
            bool arriba = hi > r.H, abajo = lo < r.L;
            if (!arriba && !abajo) return;
            r.Hecha = true;
            if (arriba && abajo) { Registrar(ny, r.Nombre, i, "rompe_los_dos_niveles_sin_operacion", 0, 0, Closes[i][0], 0); return; }
            int lado = arriba ? 1 : -1; double precio = Closes[i][0];
            DateTime salida = Hora(dia, 1645);
            if (!SesionCubre(i, ahoraNT, salida)) { Registrar(ny, r.Nombre, i, "sin_entrada_cierre_de_sesion_antes_de_la_salida", 0, 0, precio, 0); return; }
            double sg = Sigma(i, hIni, 1645, 0, 60, ny);
            int q = Contratos(i, RiesgoPct / 100.0 * PesoDiarias, sg, precio);
            if (q <= 0) { Registrar(ny, r.Nombre, i, "sin_entrada_0_contratos", 0, sg, precio, 0); return; }
            double stop, obj;
            if (r.Asiatica) { double w = r.H - r.L; stop = lado > 0 ? r.L : r.H; obj = precio + lado * w; }
            else { stop = precio - lado * r.Atr; obj = precio + lado * 3 * r.Atr; }
            posiciones.Add(new Pos { Estrategia = r.Nombre, Mercado = i, Contratos = lado * q, Entrada = precio, Stop = stop, Objetivo = obj, SalidaNY = salida, Sigma = sg, EntradaNY = ny });
            Registrar(ny, r.Nombre, i, (lado > 0 ? "compra_ruptura_" : "venta_ruptura_") + r.H.ToString(CultureInfo.InvariantCulture) + "_" + r.L.ToString(CultureInfo.InvariantCulture), q, sg, precio, 0);
        }

        private bool PrepararNiveles(Ruptura r, DateTime dia)
        {
            Bars b = BarsArray[r.Mercado]; int fin = CurrentBars[r.Mercado];
            if (r.Asiatica)
            {
                DateTime a = Hora(dia.AddDays(-1), 1900), z = Hora(dia, 300);
                double h = double.MinValue, l = double.MaxValue; int n = 0;
                for (int k = fin; k >= 0; k--)
                {
                    DateTime t = ANY(b.GetTime(k)).AddMinutes(-1);          // inicio del minuto
                    if (t >= z) continue; if (t < a) break;
                    h = Math.Max(h, b.GetHigh(k)); l = Math.Min(l, b.GetLow(k)); n++;
                }
                if (n < 3 || h <= l) return false;
                r.H = h; r.L = l; return true;
            }
            // sesiones 17:00→17:00 NY (clave = fecha de NY + 7 h) anteriores a la de hoy
            DateTime hoyClave = dia;   // la sesión de hoy empieza ayer a las 17:00
            var ses = new List<double[]>();   // {máx, mín, cierre} de las sesiones anteriores, de la más reciente a la más antigua
            DateTime clave = DateTime.MinValue; double sh = double.MinValue, sl = double.MaxValue, sc = 0;
            for (int k = fin; k >= 0 && ses.Count < 16; k--)
            {
                DateTime t = ANY(b.GetTime(k)).AddMinutes(-1);
                DateTime c = t.AddHours(7).Date;
                if (c >= hoyClave) continue;
                if (c != clave)
                {
                    if (clave != DateTime.MinValue && Laborable(clave)) ses.Add(new[] { sh, sl, sc });
                    clave = c; sh = double.MinValue; sl = double.MaxValue; sc = b.GetClose(k);
                }
                sh = Math.Max(sh, b.GetHigh(k)); sl = Math.Min(sl, b.GetLow(k));
            }
            if (ses.Count < 15) return false;
            double tr = 0;
            for (int s = 0; s < 14; s++)
            {
                double cAnt = ses[s + 1][2];
                tr += Math.Max(ses[s][0] - ses[s][1], Math.Max(Math.Abs(ses[s][0] - cAnt), Math.Abs(ses[s][1] - cAnt)));
            }
            r.H = ses[0][0]; r.L = ses[0][1]; r.Atr = tr / 14; return r.Atr > 0;
        }

        // ---------- salidas ----------
        private void VigilarSalidas(int bip, DateTime ny)
        {
            foreach (var p in posiciones.ToList())
            {
                int i = p.Mercado; if (CurrentBars[i] < 1) continue;
                string motivo = null;
                if (ny >= p.SalidaNY) motivo = "cierre_hora";
                else if (bip == i)
                {
                    double hi = Highs[i][0], lo = Lows[i][0];
                    bool largo = p.Contratos > 0;
                    if (largo ? lo <= p.Stop : hi >= p.Stop) motivo = "cierre_stop";
                    else if (!double.IsNaN(p.Objetivo) && (largo ? hi >= p.Objetivo : lo <= p.Objetivo)) motivo = "cierre_objetivo";
                    else if (IsFirstTickOfBar && !SesionCubre(i, Times[i][0], p.SalidaNY.AddMinutes(5))) motivo = "cierre_antes_de_cierre_de_sesion";
                }
                if (motivo == null) continue;
                double px = Closes[i][0];
                double pnl = (px - p.Entrada) * p.Contratos * Instruments[i].MasterInstrument.PointValue;
                posiciones.Remove(p);
                Registrar(ny, p.Estrategia, i, motivo, Math.Abs(p.Contratos), p.Sigma, px, pnl);
            }
        }

        // ---------- posición neta ----------
        private void Reconciliar(DateTime ny)
        {
            if (State != State.Realtime && !PermitirHistorico) return;
            for (int i = 1; i < BarsArray.Length; i++)
            {
                if (pendiente[i] || CurrentBars[i] < 1) continue;
                int objetivo = posiciones.Where(p => p.Mercado == i).Sum(p => p.Contratos);
                int actual = Positions[i].MarketPosition == MarketPosition.Long ? Positions[i].Quantity
                           : Positions[i].MarketPosition == MarketPosition.Short ? -Positions[i].Quantity : 0;
                int dif = objetivo - actual; if (dif == 0) continue;
                OrderAction acc; int q;
                if (dif > 0) { if (actual < 0) { acc = OrderAction.BuyToCover; q = Math.Min(dif, -actual); } else { acc = OrderAction.Buy; q = dif; } }
                else { if (actual > 0) { acc = OrderAction.Sell; q = Math.Min(-dif, actual); } else { acc = OrderAction.SellShort; q = -dif; } }
                pendiente[i] = true;
                SubmitOrderUnmanaged(i, acc, OrderType.Market, q, 0, 0, "", "neto_" + i);
            }
        }

        protected override void OnOrderUpdate(Order order, double limitPrice, double stopPrice, int quantity, int filled, double averageFillPrice,
                                              OrderState orderState, DateTime time, ErrorCode error, string comment)
        {
            if (order == null || order.Name == null || !order.Name.StartsWith("neto_")) return;
            int i; if (!int.TryParse(order.Name.Substring(5), out i) || i >= pendiente.Length) return;
            if (orderState == OrderState.Filled || orderState == OrderState.Cancelled || orderState == OrderState.Rejected)
            {
                pendiente[i] = false;
                if (orderState != OrderState.Filled)
                    Registrar(ANY(time), "cartera", i, "orden_" + orderState + "_" + error + "_" + (comment ?? "").Replace(",", ";"), quantity, 0, 0, 0);
            }
        }
    }
}
