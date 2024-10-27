const { Component, whenReady, xml, mount, onMounted } = owl;

class PrintComponent extends Component {
  // Class property to store fetched employee data
  employeeData = [];
  docName = '';

  setup() {
    // Fetch employee data when the component is mounted
    onMounted(() => {
      this.fetchEmployeeData();
    });
  }

  async fetchEmployeeData() {
    try {
        // Retrieve text using XPath
        const textNode = document.evaluate(
            '/html/body/div[1]/div/div/div[1]/div/div[1]/div[2]/div/div[1]/span',
            document,
            null,
            XPathResult.FIRST_ORDERED_NODE_TYPE,
            null
        ).singleNodeValue;

        const text = textNode ? textNode.textContent.trim() : '';
        if (!text) {
            console.warn('Text content is empty or could not be retrieved.');
            return; // Exit if `text` is empty or undefined
        }

        console.log('Document name to search:', text);

        const url = '/web/dataset/call_kw'; // Odoo's JSON-RPC endpoint

        const requestPayload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "model": "certificate.of.employment",
                "method": "search_read",
                "args": [], // args can be left empty since domain is provided in kwargs
                "kwargs": {
                    "fields": ["id", "doc_name", "company_id", "department", "first_name", "last_name"],
                    "domain": [["doc_name", "=", text]]
                }
            }
        };

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestPayload),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        if (data.error) {
            console.error('Error in Odoo response:', data.error);
            return;
        }

        this.employeeData = data.result || []; // Store fetched data in component state, or empty array if null
        console.log('Fetched employee data:', this.employeeData);

    } catch (error) {
        console.error("Error fetching employee data:", error);
    }
}

  async onPrint() {
  
    
    if (!this.employeeData || this.employeeData.length === 0) {
      console.error("No employee data available to print.");
      alert("Employee data is not available to print."); // Show an alert to the user
      return; // Exit the function if no data
    }
  
    const printWindow = window.open('', '', 'width=800,height=600'); // Open a new window
  
    // Write the content to the new window, including employee data
    const employee = this.employeeData[0];
    printWindow.document.write(`
      <html>
        <head>
          <title>Print</title>
          <style>
            body { font-family: Arial, sans-serif; }
            .content-title { text-transform: uppercase; font-weight: bold; font-size: 18px; margin-bottom: 20px; text-align: center; }
            .content-container { margin: 0 100px; }
            .content p { line-height: 1.6; text-indent: 40px; margin-bottom: 15px; text-align: justify; }
          </style>
        </head>
        <body>
          <main>
            <div class="header"></div>
            <div class="content-container">
              <div class="content-title">Certification</div>
              <div class="content">
                <p>This is to certify that Mr./Ms. ${employee.first_name} ${employee.last_name} is a permanent employee of,  a corporation duly registered and existing under Philippine Laws.</p>
                <p>Mr./Ms. ${employee.last_name} has been employed since (date hired). He/She presently holds the position of (position) with a monthly compensation of (monthly rate + dma + ntax allow).</p>
                <p>This certification is being issued upon the request of Mr./Ms. ${employee.last_name} for his/her bank loan application.</p>
                <p>Should you have any further query that requires confirmation, please feel free to contact us at 02-89481528 or 0917-528-8038.</p>
                <p>Signed this (date prepared).</p>
              </div>
            </div>
          </main>
        </body>
      </html>
    `);
  
    printWindow.document.close(); // Close the document writing
    printWindow.focus(); // Focus the new window
    printWindow.print(); // Trigger the print dialog
    printWindow.close(); // Close the print window after printing
  }
  
}

// Define the template for the PrintComponent
PrintComponent.template = xml`
  <button t-on-click="onPrint" class="btn btn-success">
    Print
  </button>
`;

// Function to mount the component or observe the DOM
function mountComponent() {
  const jsElement = document.querySelector('.js_template_using_owl');

  if (jsElement instanceof HTMLElement) {
    // Ensure jsElement is a valid DOM element before attempting to mount the component
    mount(PrintComponent, {
      target: jsElement
    });
  } else {
    // Create a MutationObserver to wait for the element to appear
    const observer = new MutationObserver(() => {
      const foundElement = document.querySelector('.js_template_using_owl');

      if (foundElement instanceof HTMLElement) {
        console.log('Found Element', foundElement)
        // Ensure foundElement is a valid DOM element before attempting to mount the component
        mount(PrintComponent, foundElement);
        observer.disconnect(); // Stop observing once the element is found and component is mounted
      }
    });

    observer.observe(document.body, { childList: true, subtree: true });
  }
}

// Wait until the DOM is fully loaded
window.onload = () => whenReady(mountComponent);
