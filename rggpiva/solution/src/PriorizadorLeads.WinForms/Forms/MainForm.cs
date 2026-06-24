using System.ComponentModel;
using System.Globalization;
using PriorizadorLeads.WinForms.Models;
using PriorizadorLeads.WinForms.Services;

namespace PriorizadorLeads.WinForms.Forms;

public sealed class MainForm : Form
{
    private readonly ComboBox _regionalFilter = CreateComboBox();
    private readonly ComboBox _managerFilter = CreateComboBox();
    private readonly ComboBox _sellerFilter = CreateComboBox();
    private readonly ComboBox _stageFilter = CreateComboBox();
    private readonly ComboBox _productFilter = CreateComboBox();
    private readonly ComboBox _sectorFilter = CreateComboBox();
    private readonly CheckBox _onlyOpenCheck = new() { Text = "Somente oportunidades abertas", Checked = true, AutoSize = true };
    private readonly NumericUpDown _minScore = new() { Minimum = 0, Maximum = 100, Increment = 5, Width = 80 };

    private readonly Label _kpiDeals = CreateKpiLabel();
    private readonly Label _kpiAvgScore = CreateKpiLabel();
    private readonly Label _kpiA = CreateKpiLabel();
    private readonly Label _kpiPipeline = CreateKpiLabel();
    private readonly Label _kpiExpected = CreateKpiLabel();
    private readonly Label _calibrationLabel = new() { AutoSize = false, Height = 110, Dock = DockStyle.Top };
    private readonly TextBox _mlSummaryText = CreateReadOnlyTextBox(200);
    private readonly DataGridView _grid = new();
    private readonly DataGridView _breakdownGrid = new();
    private readonly TextBox _dealSummary = CreateReadOnlyTextBox(76);
    private readonly TextBox _whyText = CreateReadOnlyTextBox(70);
    private readonly TextBox _riskText = CreateReadOnlyTextBox(70);
    private readonly TextBox _actionText = CreateReadOnlyTextBox(70);
    private readonly StatusStrip _status = new();
    private readonly ToolStripStatusLabel _statusLabel = new("Carregando dados...");

    private List<ScoredOpportunity> _all = new();
    private List<ScoredOpportunity> _current = new();
    private ScoringReferences _refs = new();
    private MlTrainingSummary _mlSummary = new();

    public MainForm()
    {
        Text = "Priorizador de Leads — Assistente de Foco Comercial | Visual Studio 2022";
        StartPosition = FormStartPosition.CenterScreen;
        WindowState = FormWindowState.Maximized;
        MinimumSize = new Size(1280, 780);
        Font = new Font("Segoe UI", 9F);

        BuildLayout();
        Load += (_, _) => LoadData();
    }

    private void BuildLayout()
    {
        _status.Items.Add(_statusLabel);

        var root = new TableLayoutPanel
        {
            Dock = DockStyle.Fill,
            ColumnCount = 2,
            RowCount = 1,
            Padding = new Padding(10)
        };
        root.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 280));
        root.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        Controls.Add(root);
        Controls.Add(_status);

        root.Controls.Add(BuildFilterPanel(), 0, 0);
        root.Controls.Add(BuildMainPanel(), 1, 0);
    }

    private Control BuildFilterPanel()
    {
        var panel = new Panel
        {
            Dock = DockStyle.Fill,
            Padding = new Padding(12),
            BackColor = Color.FromArgb(248, 248, 248)
        };

        var title = new Label
        {
            Text = "Filtros",
            Font = new Font(Font, FontStyle.Bold),
            Dock = DockStyle.Top,
            Height = 30
        };
        panel.Controls.Add(title);

        var filters = new TableLayoutPanel
        {
            Dock = DockStyle.Top,
            ColumnCount = 1,
            RowCount = 20,
            AutoSize = true,
            Padding = new Padding(0, 4, 0, 4)
        };
        panel.Controls.Add(filters);
        filters.BringToFront();

        AddFilter(filters, "Regional", _regionalFilter);
        AddFilter(filters, "Gerente", _managerFilter);
        AddFilter(filters, "Vendedor", _sellerFilter);
        AddFilter(filters, "Etapa", _stageFilter);
        AddFilter(filters, "Produto", _productFilter);
        AddFilter(filters, "Setor", _sectorFilter);

        filters.Controls.Add(_onlyOpenCheck);
        filters.Controls.Add(new Label { Text = "Score mínimo", AutoSize = true, Margin = new Padding(0, 12, 0, 0) });
        filters.Controls.Add(_minScore);

        var apply = new Button { Text = "Aplicar filtros", Height = 34, Dock = DockStyle.Top, Margin = new Padding(0, 14, 0, 0) };
        apply.Click += (_, _) => ApplyFilters();
        filters.Controls.Add(apply);

        var clear = new Button { Text = "Limpar filtros", Height = 34, Dock = DockStyle.Top, Margin = new Padding(0, 6, 0, 0) };
        clear.Click += (_, _) => ClearFilters();
        filters.Controls.Add(clear);

        var export = new Button { Text = "Exportar CSV atual", Height = 34, Dock = DockStyle.Top, Margin = new Padding(0, 6, 0, 0) };
        export.Click += (_, _) => ExportCurrentCsv();
        filters.Controls.Add(export);

        var help = new TextBox
        {
            Multiline = true,
            ReadOnly = true,
            BorderStyle = BorderStyle.None,
            BackColor = panel.BackColor,
            Dock = DockStyle.Bottom,
            Height = 180,
            Text = "Uso esperado:\r\n" +
                   "1. Filtre por regional, gerente ou vendedor.\r\n" +
                   "2. Consulte a lista já ordenada por score híbrido.\r\n" +
                   "3. Selecione uma oportunidade para entender regras + ML.\r\n" +
                   "4. Use a próxima ação como orientação de contato."
        };
        panel.Controls.Add(help);

        return panel;
    }

    private Control BuildMainPanel()
    {
        var panel = new TableLayoutPanel
        {
            Dock = DockStyle.Fill,
            RowCount = 4,
            ColumnCount = 1
        };
        panel.RowStyles.Add(new RowStyle(SizeType.Absolute, 48));
        panel.RowStyles.Add(new RowStyle(SizeType.Absolute, 82));
        panel.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        panel.RowStyles.Add(new RowStyle(SizeType.Absolute, 255));

        var title = new Label
        {
            Text = "Priorizador de Leads — Assistente de Foco Comercial",
            Font = new Font("Segoe UI", 16F, FontStyle.Bold),
            Dock = DockStyle.Fill,
            TextAlign = ContentAlignment.MiddleLeft
        };
        panel.Controls.Add(title, 0, 0);

        var kpiPanel = new FlowLayoutPanel
        {
            Dock = DockStyle.Fill,
            FlowDirection = FlowDirection.LeftToRight,
            WrapContents = false,
            AutoScroll = true
        };
        kpiPanel.Controls.AddRange(new Control[] { _kpiDeals, _kpiAvgScore, _kpiA, _kpiPipeline, _kpiExpected });
        panel.Controls.Add(kpiPanel, 0, 1);

        ConfigureGrid();
        panel.Controls.Add(_grid, 0, 2);

        panel.Controls.Add(BuildDetailPanel(), 0, 3);
        return panel;
    }

    private Control BuildDetailPanel()
    {
        var tab = new TabControl { Dock = DockStyle.Fill };

        var detail = new TabPage("Detalhe da oportunidade");
        var detailLayout = new TableLayoutPanel
        {
            Dock = DockStyle.Fill,
            RowCount = 4,
            ColumnCount = 2,
            Padding = new Padding(8)
        };
        detailLayout.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 150));
        detailLayout.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        detailLayout.RowStyles.Add(new RowStyle(SizeType.Absolute, 76));
        detailLayout.RowStyles.Add(new RowStyle(SizeType.Absolute, 70));
        detailLayout.RowStyles.Add(new RowStyle(SizeType.Absolute, 70));
        detailLayout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        detail.Controls.Add(detailLayout);

        AddDetailRow(detailLayout, 0, "Resumo", _dealSummary);
        AddDetailRow(detailLayout, 1, "Justificativa", _whyText);
        AddDetailRow(detailLayout, 2, "Riscos", _riskText);
        AddDetailRow(detailLayout, 3, "Próxima ação", _actionText);
        tab.TabPages.Add(detail);

        var breakdown = new TabPage("Componentes do score");
        ConfigureBreakdownGrid();
        breakdown.Controls.Add(_breakdownGrid);
        tab.TabPages.Add(breakdown);

        var logic = new TabPage("Lógica e calibragem");
        var logicText = CreateReadOnlyTextBox(200);
        logicText.Dock = DockStyle.Fill;
        logicText.Text = "O score explicável combina: etapa da oportunidade (20%), vendedor/gerente/regional (18%), conta/porte (18%), produto/série (16%), setor (12%), velocidade/idade da oportunidade (10%) e valor potencial (6%).\r\n\r\n" +
                         "Além dele, a aplicação treina um modelo supervisionado ML.NET FastTree usando oportunidades fechadas. O alvo é Ganha ou Perdida.\r\n\r\n" +
                         "A etapa do negócio não entra como feature do modelo para evitar vazamento de informação, pois Ganha/Perdida é o próprio resultado final.\r\n\r\n" +
                         "O ranking final usa score híbrido: 55% score explicável + 45% probabilidade ML. Assim a ferramenta preserva interpretabilidade e adiciona aprendizado estatístico.";
        logic.Controls.Add(logicText);
        tab.TabPages.Add(logic);

        var mlTab = new TabPage("Modelo ML.NET");
        _mlSummaryText.Dock = DockStyle.Fill;
        mlTab.Controls.Add(_mlSummaryText);
        tab.TabPages.Add(mlTab);

        var calibration = new TabPage("Dados de referência");
        _calibrationLabel.Padding = new Padding(10);
        calibration.Controls.Add(_calibrationLabel);
        tab.TabPages.Add(calibration);

        return tab;
    }

    private void LoadData()
    {
        try
        {
            var dataDir = FindDataDirectory();
            var data = CsvLoader.Load(dataDir);
            var result = new ScoringEngine().Score(data);
            _all = result.Opportunities;
            _refs = result.References;

            try
            {
                _mlSummary = new MachineLearningLeadScorer().TrainAndApply(_all);
            }
            catch (Exception mlEx)
            {
                foreach (var row in _all)
                {
                    row.HybridScore = row.Score;
                    row.HybridExpectedValue = row.ExpectedValue;
                    row.MlWinProbability = row.Score / 100d;
                    row.MlBand = "ML indisponível";
                    row.MlExplanation = "Modelo ML não foi aplicado. Usando somente score explicável.";
                }

                _mlSummary = new MlTrainingSummary
                {
                    IsAvailable = false,
                    StatusMessage = "Falha ao treinar/aplicar ML.NET: " + mlEx.Message,
                    ClosedRows = _all.Count(x => x.IsClosed),
                    TrainedAt = DateTime.Now,
                    Notes = new List<string> { mlEx.ToString() }
                };
            }

            _all = _all
                .OrderByDescending(x => x.HybridScore > 0 ? x.HybridScore : x.Score)
                .ThenByDescending(x => x.HybridExpectedValue > 0 ? x.HybridExpectedValue : x.ExpectedValue)
                .ToList();

            LoadFilterValues();
            UpdateCalibrationLabel();
            UpdateMlSummaryText();
            ApplyFilters();
            _statusLabel.Text = $"Dados carregados de {dataDir}. Total de oportunidades: {_all.Count:N0}. Modelo ML: {_mlSummary.StatusMessage}";
        }
        catch (Exception ex)
        {
            _statusLabel.Text = "Erro ao carregar dados.";
            MessageBox.Show(this, ex.Message, "Erro ao iniciar Priorizador de Leads", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private string FindDataDirectory()
    {
        var candidates = new[]
        {
            Path.Combine(AppContext.BaseDirectory, "Data"),
            Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "Data"),
            Path.Combine(Environment.CurrentDirectory, "Data")
        };

        foreach (var candidate in candidates)
        {
            var full = Path.GetFullPath(candidate);
            if (Directory.Exists(full) && (File.Exists(Path.Combine(full, "funil_vendas.csv")) || File.Exists(Path.Combine(full, "sales_pipeline.csv"))))
                return full;
        }

        return Path.Combine(AppContext.BaseDirectory, "Data");
    }

    private void LoadFilterValues()
    {
        LoadCombo(_regionalFilter, _all.Select(x => x.RegionalOffice));
        LoadCombo(_managerFilter, _all.Select(x => x.Manager));
        LoadCombo(_sellerFilter, _all.Select(x => x.SalesAgent));
        LoadStageCombo(_stageFilter);
        LoadCombo(_productFilter, _all.Select(x => x.Product));
        LoadCombo(_sectorFilter, _all.Select(x => x.Sector));
    }

    private static void LoadCombo(ComboBox combo, IEnumerable<string> values)
    {
        combo.Items.Clear();
        combo.Items.Add("Todos");
        foreach (var value in values.Where(x => !string.IsNullOrWhiteSpace(x)).Distinct(StringComparer.OrdinalIgnoreCase).OrderBy(x => x))
            combo.Items.Add(value);
        combo.SelectedIndex = 0;
    }

    private static void LoadStageCombo(ComboBox combo)
    {
        combo.Items.Clear();
        combo.Items.Add("Todos");
        combo.Items.Add("Prospecção");
        combo.Items.Add("Em negociação");
        combo.Items.Add("Ganha");
        combo.Items.Add("Perdida");
        combo.SelectedIndex = 0;
    }

    private void ApplyFilters()
    {
        IEnumerable<ScoredOpportunity> query = _all;

        if (_onlyOpenCheck.Checked)
            query = query.Where(x => x.IsOpen);

        query = query.Where(x => (x.HybridScore > 0 ? x.HybridScore : x.Score) >= (double)_minScore.Value);
        query = ApplyComboFilter(query, _regionalFilter, x => x.RegionalOffice);
        query = ApplyComboFilter(query, _managerFilter, x => x.Manager);
        query = ApplyComboFilter(query, _sellerFilter, x => x.SalesAgent);
        query = ApplyStageFilter(query, _stageFilter);
        query = ApplyComboFilter(query, _productFilter, x => x.Product);
        query = ApplyComboFilter(query, _sectorFilter, x => x.Sector);

        _current = query
            .OrderByDescending(x => x.HybridScore > 0 ? x.HybridScore : x.Score)
            .ThenByDescending(x => x.HybridExpectedValue > 0 ? x.HybridExpectedValue : x.ExpectedValue)
            .ToList();

        _grid.DataSource = new BindingList<ScoredOpportunity>(_current);
        UpdateKpis();
        UpdateDetailFromSelection();
        _statusLabel.Text = $"Exibindo {_current.Count:N0} oportunidade(s).";
    }

    private static IEnumerable<ScoredOpportunity> ApplyComboFilter(IEnumerable<ScoredOpportunity> source, ComboBox combo, Func<ScoredOpportunity, string> selector)
    {
        if (combo.SelectedItem is not string selected || selected == "Todos")
            return source;
        return source.Where(x => selector(x).Equals(selected, StringComparison.OrdinalIgnoreCase));
    }

    private static IEnumerable<ScoredOpportunity> ApplyStageFilter(IEnumerable<ScoredOpportunity> source, ComboBox combo)
    {
        if (combo.SelectedItem is not string selected || selected == "Todos")
            return source;

        return source.Where(x => x.EtapaPtBr.Equals(selected, StringComparison.OrdinalIgnoreCase));
    }

    private void ClearFilters()
    {
        foreach (var combo in new[] { _regionalFilter, _managerFilter, _sellerFilter, _stageFilter, _productFilter, _sectorFilter })
            combo.SelectedIndex = 0;
        _onlyOpenCheck.Checked = true;
        _minScore.Value = 0;
        ApplyFilters();
    }

    private void ExportCurrentCsv()
    {
        if (_current.Count == 0)
        {
            MessageBox.Show(this, "Não há linhas para exportar com os filtros atuais.", "Exportação", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        using var dialog = new SaveFileDialog
        {
            Title = "Exportar prioridades",
            Filter = "CSV (*.csv)|*.csv",
            FileName = "prioridades_oportunidades_abertas_ptbr_ml.csv"
        };

        if (dialog.ShowDialog(this) == DialogResult.OK)
        {
            ReportExporter.ExportPrioritiesCsv(_current, dialog.FileName);
            _statusLabel.Text = $"CSV exportado: {dialog.FileName}";
            MessageBox.Show(this, "CSV exportado com sucesso.", "Exportação", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
    }

    private void UpdateKpis()
    {
        _kpiDeals.Text = $"Oportunidades exibidas\r\n{_current.Count:N0}";
        _kpiAvgScore.Text = $"Score híbrido médio\r\n{(_current.Count == 0 ? 0 : _current.Average(x => x.HybridScore > 0 ? x.HybridScore : x.Score)):0.0}";
        _kpiA.Text = $"A - Focar hoje\r\n{_current.Count(x => x.PriorityBand == "A - Focar hoje"):N0}";
        _kpiPipeline.Text = $"Pipeline potencial\r\n{Money(_current.Sum(x => x.EstimatedDealValue))}";
        _kpiExpected.Text = $"Valor ponderado híbrido\r\n{Money(_current.Sum(x => x.HybridExpectedValue > 0 ? x.HybridExpectedValue : x.ExpectedValue))}";
    }

    private void UpdateCalibrationLabel()
    {
        _calibrationLabel.Text =
            $"Taxa histórica de ganho: {_refs.GlobalWinRate:P1}\r\n" +
            $"Ciclo mediano das oportunidades ganhas: {_refs.MedianWonCycleDays:0} dias\r\n" +
            $"Data de referência do dataset: {_refs.ReferenceDate:yyyy-MM-dd}\r\n" +
            $"Oportunidades abertas: {_refs.OpenCount:N0}\r\n" +
            $"Oportunidades fechadas: {_refs.ClosedCount:N0}\r\n\r\n" +
            string.Join("\r\n", _refs.DataQualityNotes.Select(x => "• " + x));
    }

    private void UpdateMlSummaryText()
    {
        var lines = new List<string>
        {
            _mlSummary.StatusMessage,
            string.Empty,
            $"Treinado em: {_mlSummary.TrainedAt:dd/MM/yyyy HH:mm:ss}",
            $"Oportunidades fechadas usadas como base: {_mlSummary.ClosedRows:N0}",
            $"Linhas treino: {_mlSummary.TrainRows:N0}",
            $"Linhas teste: {_mlSummary.TestRows:N0}",
            string.Empty,
            $"Acurácia: {_mlSummary.Accuracy:P1}",
            $"AUC ROC: {_mlSummary.AreaUnderRocCurve:0.000}",
            $"AUC Precision-Recall: {_mlSummary.AreaUnderPrecisionRecallCurve:0.000}",
            $"F1-Score: {_mlSummary.F1Score:0.000}",
            $"Log Loss: {_mlSummary.LogLoss:0.000}",
            string.Empty,
            "Features usadas:",
            string.Join("\r\n", _mlSummary.FeaturesUsed.Select(x => "• " + x)),
            string.Empty,
            "Notas:",
            string.Join("\r\n", _mlSummary.Notes.Select(x => "• " + x))
        };

        _mlSummaryText.Text = string.Join("\r\n", lines);
    }

    private void UpdateDetailFromSelection()
    {
        var row = SelectedOpportunity();
        if (row == null)
        {
            _dealSummary.Text = "Nenhuma oportunidade selecionada.";
            _whyText.Clear();
            _riskText.Clear();
            _actionText.Clear();
            _breakdownGrid.DataSource = null;
            return;
        }

        var ageText = row.DealAgeDays.HasValue ? $"{row.DealAgeDays.Value:N0} dias" : "não informada";
        _dealSummary.Text =
            $"{row.OpportunityId} | {row.PriorityBand} | Score híbrido {row.HybridScore:0.0} | ML {row.MlWinProbability:P1}\r\n" +
            $"Vendedor: {row.SalesAgent} | Gerente: {row.Manager} | Regional: {row.RegionalOffice}\r\n" +
            $"Conta/setor: {row.Account} / {row.Sector} | Produto/etapa: {row.Product} / {row.EtapaPtBr}\r\n" +
            $"Valor potencial: {Money(row.EstimatedDealValue)} | Valor ponderado híbrido: {Money(row.HybridExpectedValue > 0 ? row.HybridExpectedValue : row.ExpectedValue)} | Idade: {ageText}";
        _whyText.Text = row.MlExplanation + "\r\n\r\nRegras: " + row.WhyHighOrLow;
        _riskText.Text = row.MainRisks;
        _actionText.Text = row.NextBestAction;
        _breakdownGrid.DataSource = new BindingList<ComponentBreakdown>(ScoringEngine.GetBreakdown(row));
    }

    private ScoredOpportunity? SelectedOpportunity()
    {
        if (_grid.CurrentRow?.DataBoundItem is ScoredOpportunity row)
            return row;
        return _current.FirstOrDefault();
    }

    private void ConfigureGrid()
    {
        _grid.Dock = DockStyle.Fill;
        _grid.ReadOnly = true;
        _grid.AllowUserToAddRows = false;
        _grid.AllowUserToDeleteRows = false;
        _grid.SelectionMode = DataGridViewSelectionMode.FullRowSelect;
        _grid.MultiSelect = false;
        _grid.AutoGenerateColumns = false;
        _grid.RowHeadersVisible = false;
        _grid.AutoSizeRowsMode = DataGridViewAutoSizeRowsMode.None;
        _grid.SelectionChanged += (_, _) => UpdateDetailFromSelection();

        AddTextColumn(_grid, nameof(ScoredOpportunity.PriorityBand), "Prioridade", 155);
        AddNumberColumn(_grid, nameof(ScoredOpportunity.HybridScore), "Score híbrido", 95, "0.0");
        AddNumberColumn(_grid, nameof(ScoredOpportunity.MlWinProbability), "Prob. ML", 85, "P1");
        AddNumberColumn(_grid, nameof(ScoredOpportunity.Score), "Score regras", 95, "0.0");
        AddNumberColumn(_grid, nameof(ScoredOpportunity.HybridExpectedValue), "Valor pond. híbrido", 130, "N0");
        AddNumberColumn(_grid, nameof(ScoredOpportunity.EstimatedDealValue), "Valor potencial", 115, "N0");
        AddTextColumn(_grid, nameof(ScoredOpportunity.OpportunityId), "ID da oportunidade", 120);
        AddTextColumn(_grid, nameof(ScoredOpportunity.EtapaPtBr), "Etapa", 115);
        AddTextColumn(_grid, nameof(ScoredOpportunity.SalesAgent), "Vendedor", 140);
        AddTextColumn(_grid, nameof(ScoredOpportunity.Manager), "Gerente", 140);
        AddTextColumn(_grid, nameof(ScoredOpportunity.RegionalOffice), "Regional", 90);
        AddTextColumn(_grid, nameof(ScoredOpportunity.Account), "Conta", 150);
        AddTextColumn(_grid, nameof(ScoredOpportunity.Sector), "Setor", 110);
        AddTextColumn(_grid, nameof(ScoredOpportunity.Product), "Produto", 130);
        AddNumberColumn(_grid, nameof(ScoredOpportunity.DealAgeDays), "Idade", 75, "N0");
        AddTextColumn(_grid, nameof(ScoredOpportunity.MlExplanation), "Explicação ML", 340);
        AddTextColumn(_grid, nameof(ScoredOpportunity.WhyHighOrLow), "Justificativa regras", 340);
        AddTextColumn(_grid, nameof(ScoredOpportunity.MainRisks), "Riscos", 300);
        AddTextColumn(_grid, nameof(ScoredOpportunity.NextBestAction), "Próxima ação", 360);
    }

    private void ConfigureBreakdownGrid()
    {
        _breakdownGrid.Dock = DockStyle.Fill;
        _breakdownGrid.ReadOnly = true;
        _breakdownGrid.AllowUserToAddRows = false;
        _breakdownGrid.AllowUserToDeleteRows = false;
        _breakdownGrid.AutoGenerateColumns = false;
        _breakdownGrid.RowHeadersVisible = false;
        _breakdownGrid.SelectionMode = DataGridViewSelectionMode.FullRowSelect;
        AddTextColumn(_breakdownGrid, nameof(ComponentBreakdown.Component), "Componente", 230);
        AddNumberColumn(_breakdownGrid, nameof(ComponentBreakdown.Score0To1), "Nota 0..1", 90, "0.000");
        AddTextColumn(_breakdownGrid, nameof(ComponentBreakdown.Interpretation), "Interpretação", 600);
    }

    private static void AddTextColumn(DataGridView grid, string property, string header, int width)
    {
        grid.Columns.Add(new DataGridViewTextBoxColumn
        {
            DataPropertyName = property,
            HeaderText = header,
            Width = width,
            SortMode = DataGridViewColumnSortMode.Automatic
        });
    }

    private static void AddNumberColumn(DataGridView grid, string property, string header, int width, string format)
    {
        grid.Columns.Add(new DataGridViewTextBoxColumn
        {
            DataPropertyName = property,
            HeaderText = header,
            Width = width,
            SortMode = DataGridViewColumnSortMode.Automatic,
            DefaultCellStyle = new DataGridViewCellStyle
            {
                Alignment = DataGridViewContentAlignment.MiddleRight,
                Format = format
            }
        });
    }

    private static void AddFilter(TableLayoutPanel panel, string label, ComboBox combo)
    {
        panel.Controls.Add(new Label { Text = label, AutoSize = true, Margin = new Padding(0, 8, 0, 0) });
        panel.Controls.Add(combo);
    }

    private static void AddDetailRow(TableLayoutPanel layout, int row, string label, TextBox textBox)
    {
        layout.Controls.Add(new Label
        {
            Text = label,
            Dock = DockStyle.Fill,
            TextAlign = ContentAlignment.TopLeft,
            Font = new Font(SystemFonts.MessageBoxFont, FontStyle.Bold)
        }, 0, row);
        layout.Controls.Add(textBox, 1, row);
    }

    private static ComboBox CreateComboBox()
    {
        return new ComboBox
        {
            DropDownStyle = ComboBoxStyle.DropDownList,
            Width = 240,
            Margin = new Padding(0, 2, 0, 2)
        };
    }

    private static TextBox CreateReadOnlyTextBox(int height)
    {
        return new TextBox
        {
            Multiline = true,
            ReadOnly = true,
            BorderStyle = BorderStyle.FixedSingle,
            ScrollBars = ScrollBars.Vertical,
            Dock = DockStyle.Fill,
            Height = height
        };
    }

    private static Label CreateKpiLabel()
    {
        return new Label
        {
            AutoSize = false,
            Width = 190,
            Height = 68,
            Padding = new Padding(10),
            Margin = new Padding(0, 0, 10, 0),
            BackColor = Color.FromArgb(238, 242, 247),
            Font = new Font("Segoe UI", 9.5F, FontStyle.Bold),
            TextAlign = ContentAlignment.MiddleLeft
        };
    }

    private static string Money(double value)
    {
        return "US$ " + value.ToString("N0", CultureInfo.InvariantCulture);
    }
}
