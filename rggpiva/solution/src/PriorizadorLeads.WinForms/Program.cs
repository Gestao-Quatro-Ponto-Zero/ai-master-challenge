using PriorizadorLeads.WinForms.Forms;

namespace PriorizadorLeads.WinForms;

internal static class Program
{
    [STAThread]
    private static void Main()
    {
        ApplicationConfiguration.Initialize();
        Application.Run(new MainForm());
    }
}
