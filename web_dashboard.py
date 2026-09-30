from http.server import BaseHTTPRequestHandler, HTTPServer
import json

from dashboard_state import get_nodes


HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>TATHACK Blockchain Simulator</title>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            background: #f4f6f8;
            color: #111827;
        }

        .container {
            max-width: 1100px;
            margin: auto;
            padding: 35px 25px;
        }

        h1 {
            text-align: center;
            margin-bottom: 35px;
            font-size: 36px;
        }

        .cards {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 15px;
        }

        .card {
            background: white;
            padding: 20px;
            border-radius: 14px;
            box-shadow: 0 3px 12px rgba(0,0,0,0.10);
        }

        .card h3 {
            margin-top: 0;
            font-size: 16px;
            color: #555;
        }

        .card h2 {
            font-size: 28px;
            margin: 15px 0;
        }

        .card p {
            margin-bottom: 0;
            color: #666;
        }

        .status-card {
            margin-top: 20px;
        }

        .online {
            color: #16a34a;
            font-weight: bold;
        }

        .section-title {
            margin-top: 35px;
            margin-bottom: 15px;
        }

        /* --------------------------------
           NORMAL NODE
        -------------------------------- */

        .node {
            background: white;
            padding: 25px;
            margin-top: 15px;
            border-radius: 14px;
            box-shadow: 0 3px 12px rgba(0,0,0,0.10);
            border: 2px solid transparent;
        }

        .node h2 {
            margin-top: 0;
        }

        /* --------------------------------
           MALICIOUS NODE
        -------------------------------- */

        .node.malicious {
            border: 2px solid #ef4444;
            background: #fff7f7;
        }

        .node.malicious h2 {
            color: #b91c1c;
        }

        .badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            background: #dcfce7;
            color: #15803d;
            font-weight: bold;
        }

        /* Normal role badge */
        .role-normal {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            background: #e0f2fe;
            color: #0369a1;
            font-weight: bold;
        }

        /* Malicious role badge */
        .role-malicious {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            background: #fee2e2;
            color: #b91c1c;
            font-weight: bold;
        }

        .info {
            margin: 10px 0;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-top: 20px;
        }

        .stat {
            background: #f8fafc;
            padding: 15px;
            border-radius: 10px;
        }

        .stat h4 {
            margin: 0 0 8px 0;
            color: #555;
        }

        .stat p {
            margin: 0;
            font-size: 22px;
            font-weight: bold;
        }

        @media (max-width: 900px) {

            .cards {
                grid-template-columns: repeat(2, 1fr);
            }

        }

        @media (max-width: 600px) {

            .cards {
                grid-template-columns: 1fr;
            }

            .stats {
                grid-template-columns: 1fr;
            }

        }

    </style>
</head>

<body>

<div class="container">

    <h1>TATHACK Blockchain Simulator</h1>

    <div class="cards">

        <div class="card">
            <h3>Network</h3>
            <h2>TATHACK</h2>
            <p>Blockchain simulation room</p>
        </div>

        <div class="card">
            <h3>Total Nodes</h3>
            <h2 id="nodeCount">0</h2>
            <p>Active blockchain nodes</p>
        </div>

        <div class="card">
            <h3>Total Blocks</h3>
            <h2 id="blockCount">0</h2>
            <p>Blocks in the network</p>
        </div>

        <div class="card">
            <h3>Total Transactions</h3>
            <h2 id="transactionCount">0</h2>
            <p>Recorded transactions</p>
        </div>

        <div class="card">
            <h3>Consensus</h3>
            <h2 id="consensus">PoW</h2>
            <p>Active consensus mechanism</p>
        </div>

    </div>

    <div class="card status-card">
        <h3>Network Status</h3>
        <h2 class="online">Online</h2>
        <p>Blockchain network is running</p>
    </div>

    <h2 class="section-title">Participating Nodes</h2>

    <div id="nodes">
        Loading nodes...
    </div>

</div>


<script>

async function loadNodes() {

    try {

        const response = await fetch("/api/nodes");
        const data = await response.json();

        const nodeNames = Object.keys(data);

        // --------------------------------
        // Total nodes
        // --------------------------------

        document.getElementById("nodeCount").innerText =
            nodeNames.length;


        // --------------------------------
        // Calculate network totals
        // --------------------------------

        let totalBlocks = 0;
        let totalTransactions = 0;

        let consensusSet = new Set();

        for (const [name, node] of Object.entries(data)) {

            totalBlocks += Number(node.blocks || 0);

            totalTransactions += Number(
                node.transactions || 0
            );

            if (node.consensus) {
                consensusSet.add(node.consensus);
            }
        }


        document.getElementById("blockCount").innerText =
            totalBlocks;

        document.getElementById("transactionCount").innerText =
            totalTransactions;

        document.getElementById("consensus").innerText =
            consensusSet.size > 0
                ? Array.from(consensusSet).join(" / ")
                : "Unknown";


        // --------------------------------
        // Node cards
        // --------------------------------

        let html = "";

        for (const [name, node] of Object.entries(data)) {

            const role =
                node.role || "Normal";

            const isMalicious =
                role.toLowerCase() === "malicious";


            const nodeClass =
                isMalicious
                    ? "node malicious"
                    : "node";


            const roleClass =
                isMalicious
                    ? "role-malicious"
                    : "role-normal";


            const roleText =
                isMalicious
                    ? "⚠ MALICIOUS"
                    : "NORMAL";


            html += `
                <div class="${nodeClass}">

                    <h2>${name}</h2>

                    <p class="info">
                        <b>Address:</b>
                        ${node.host}:${node.port}
                    </p>

                    <p class="info">
                        <b>Consensus:</b>
                        ${node.consensus || "Unknown"}
                    </p>

                    <p class="info">
                        <b>Role:</b>
                        <span class="${roleClass}">
                            ${roleText}
                        </span>
                    </p>

                    <p class="info">
                        <b>Status:</b>
                        <span class="badge">
                            ${node.status || "Unknown"}
                        </span>
                    </p>

                    <div class="stats">

                        <div class="stat">
                            <h4>Connected Peers</h4>
                            <p>${node.peers || 0}</p>
                        </div>

                        <div class="stat">
                            <h4>Blocks</h4>
                            <p>${node.blocks || 0}</p>
                        </div>

                        <div class="stat">
                            <h4>Transactions</h4>
                            <p>${node.transactions || 0}</p>
                        </div>

                    </div>

                </div>
            `;
        }


        // --------------------------------
        // No nodes
        // --------------------------------

        if (nodeNames.length === 0) {

            html = `
                <div class="node">
                    <p>
                        No blockchain nodes are currently connected.
                    </p>
                </div>
            `;
        }


        document.getElementById("nodes").innerHTML =
            html;


    } catch (error) {

        document.getElementById("nodes").innerHTML =
            "<p>Unable to connect to dashboard server.</p>";

        console.error(error);
    }
}


loadNodes();


// Refresh every 3 seconds
setInterval(loadNodes, 3000);

</script>

</body>
</html>
"""


class DashboardHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        if self.path == "/":

            self.send_response(200)

            self.send_header(
                "Content-type",
                "text/html; charset=utf-8"
            )

            self.end_headers()

            self.wfile.write(
                HTML.encode("utf-8")
            )


        elif self.path == "/api/nodes":

            self.send_response(200)

            self.send_header(
                "Content-type",
                "application/json; charset=utf-8"
            )

            self.end_headers()

            nodes = get_nodes()

            self.wfile.write(
                json.dumps(nodes).encode("utf-8")
            )


        else:

            self.send_response(404)
            self.end_headers()


server = HTTPServer(
    ("localhost", 8080),
    DashboardHandler
)


print("========================================")
print("     TATHACK WEB DASHBOARD")
print("========================================")
print()
print("Dashboard running at:")
print("http://localhost:8080")
print()
print("Press CTRL+C to stop.")


try:

    server.serve_forever()

except KeyboardInterrupt:

    print("\nDashboard stopped.")
    server.server_close()