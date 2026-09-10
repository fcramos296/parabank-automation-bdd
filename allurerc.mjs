import { env } from "node:process";

const isGitHubActions = env.GITHUB_ACTIONS === "true";

const workflowUrl =
  isGitHubActions &&
  env.GITHUB_SERVER_URL &&
  env.GITHUB_REPOSITORY &&
  env.GITHUB_RUN_ID
    ? `${env.GITHUB_SERVER_URL}/${env.GITHUB_REPOSITORY}/actions/runs/${env.GITHUB_RUN_ID}`
    : undefined;

const executionName = isGitHubActions
  ? `GitHub Actions #${env.GITHUB_RUN_NUMBER ?? "-"}`
  : "Execução local";

const scope = env.ALLURE_SCOPE ?? "full";
const browser = env.ALLURE_BROWSER ?? "chromium";

export default {
  name: "Topaz | ParaBank Automation BDD",
  output: "./reports/allure-report",

  variables: {
    Projeto: "ParaBank Automation BDD",
    Empresa: "Topaz",
    Ambiente: "ParaBank local via Docker",
    Execução: executionName,
    Escopo: scope,
    Browser: browser,
    Stack: "Python + Playwright + Behave",
  },

  defaultLabels: {
    layer: "e2e",
    framework: "behave",
    language: "python",
    component: "parabank",
  },

  categories: {
    rules: [
      {
        name: "Timeout / sincronização",
        id: "timeout-sync",
        matchers: {
          statuses: ["failed", "broken"],
          message: /Timeout|timed out|TimeoutError/i,
          trace: /Timeout|timed out|TimeoutError/i,
        },
        groupBy: ["feature"],
      },
      {
        name: "Falha funcional",
        id: "functional-failure",
        matchers: {
          statuses: ["failed"],
          trace: /AssertionError|expect\(|Assertion/i,
        },
        groupBy: ["feature"],
      },
      {
        name: "Falha de automação / infraestrutura",
        id: "automation-infrastructure",
        matchers: {
          statuses: ["broken"],
        },
        groupBy: ["feature"],
      },
    ],
  },

  plugins: {
    awesome: {
      options: {
        reportName: "Topaz | ParaBank QA Automation",
        logo: "./assets/topaz-logo.png",
        theme: "dark",
        reportLanguage: "br",
        singleFile: false,
        ci:
          isGitHubActions && workflowUrl
            ? {
                type: "github",
                url: workflowUrl,
                name: `GitHub Actions #${env.GITHUB_RUN_NUMBER ?? "-"}`,
              }
            : undefined,
      },
    },
  },
};
