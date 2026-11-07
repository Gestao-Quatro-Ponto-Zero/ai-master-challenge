"use client";

import useDashboardController from "../features/workspace/use-dashboard-controller";
import Icon from "../components/ui/icon";
import Sidebar from "../components/layout/sidebar";
import AppHeader from "../components/layout/app-header";
import TodayView from "../features/today/today-view";
import PipelineView from "../features/pipeline/pipeline-view";
import ResultsView from "../features/results/results-view";
import PriorityHelp from "../features/priorities/priority-help";
import DealDialog from "../features/opportunities/opportunity-dialog";
export default function Dashboard({ data }) {
  const {
    agents,
    agent,
    view,
    events,
    ready,
    error,
    toast,
    moveAction,
    dropTarget,
    collapsed,
    dark,
    query,
    queue,
    scope,
    manager,
    region,
    limit,
    clock,
    all,
    mine,
    open,
    agenda,
    due,
    progress,
    top,
    openCounts,
    contactsToday,
    qualified,
    detail,
    scoped,
    titles,
    setView,
    setLimit,
    setQuery,
    setQueue,
    setScope,
    setManager,
    setRegion,
    setDragged,
    setDropTarget,
    setSelected,
    setMoveAction,
    setPreference,
    openDeal,
    handleDrop,
    changeAgent,
    record,
    showDailyProgress,
    exportActivities,
  } = useDashboardController(data);
  return (
    <div
      className={`app-shell ${collapsed ? "nav-collapsed" : ""} ${dark ? "theme-dark" : ""}`}
    >
      <Sidebar
        data={data}
        view={view}
        collapsed={collapsed}
        ready={ready}
        progress={progress}
        due={due}
        setView={setView}
        setLimit={setLimit}
        setPreference={setPreference}
        showDailyProgress={showDailyProgress}
      />
      <main>
        <AppHeader
          titles={titles}
          view={view}
          dark={dark}
          setPreference={setPreference}
          agents={agents}
          agent={agent}
          changeAgent={changeAgent}
          data={data}
          openCounts={openCounts}
        />
        <div className="page-content">
          {error && (
            <div className="error-banner" role="alert">
              {error}
            </div>
          )}
          <div className="context-line">
            <span className="context-pill">
              <span className="live-dot" />
              MODO DEMONSTRAÇÃO
            </span>
            <span>
              CRM de referência: 31 dez 2017{" "}
              <span className="context-dot">·</span> Atividades:{" "}
              {clock
                ? new Date(clock).toLocaleDateString("pt-BR")
                : "carregando"}
            </span>
            <button className="text-button" onClick={() => setView("method")}>
              Sobre os dados <Icon name="info" size={13} />
            </button>
          </div>
          {view === "today" && (
            <TodayView
              agent={agent}
              open={open}
              top={top}
              due={due}
              qualified={qualified}
              contactsToday={contactsToday}
              agenda={agenda}
              mine={mine}
              progress={progress}
              setSelected={setSelected}
              setView={setView}
              setQueue={setQueue}
            />
          )}
          {view === "pipeline" && (
            <PipelineView
              mine={mine}
              query={query}
              queue={queue}
              limit={limit}
              dropTarget={dropTarget}
              setQuery={setQuery}
              setQueue={setQueue}
              setLimit={setLimit}
              setDropTarget={setDropTarget}
              setDragged={setDragged}
              handleDrop={handleDrop}
              openDeal={openDeal}
            />
          )}
          {view === "results" && (
            <ResultsView
              data={data}
              agent={agent}
              all={all}
              scoped={scoped}
              scope={scope}
              manager={manager}
              region={region}
              events={events}
              setScope={setScope}
              setManager={setManager}
              setRegion={setRegion}
              exportActivities={exportActivities}
            />
          )}
          {view === "method" && <PriorityHelp data={data} />}
          <footer className="page-footer">
            <span>
              G4 Sales Priority <span>·</span> Projeto demonstrativo
              independente
            </span>
            <span>Dados reais. Prioridades explicáveis. Decisões humanas.</span>
          </footer>
        </div>
      </main>
      {toast && (
        <div className="toast" role="status">
          <Icon name="check" />
          {toast}
        </div>
      )}
      {detail && (
        <DealDialog
          key={detail.opportunity_id}
          deal={detail}
          initialAction={moveAction}
          onClose={() => {
            setSelected(null);
            setMoveAction(null);
          }}
          onRecord={(values) => record(detail, values)}
          disabled={!ready || !!error}
        />
      )}
    </div>
  );
}
