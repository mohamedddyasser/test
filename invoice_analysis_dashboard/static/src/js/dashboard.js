/** @odoo-module */

import {registry} from '@web/core/registry';

const {Component, onMounted, useState, useRef} = owl;
import {jsonrpc} from "@web/core/network/rpc_service";

export class InvoiceAnalysisDashboard extends Component {
    setup() {
        this.invoice_line_chart_ref = useRef("invoice_line_chart_ref");
        this.chartInstance = null;  // To store the Chart.js instance
        this.state = useState({
            selectedYear: null,  // Selected year for the chart
            availableYears: []   // List of years available from the data
        });
        onMounted(this.onMounted);
    }

    async onMounted() {
        await this.loadAvailableYears();  // Load available years when the component mounts
        if (this.state.availableYears.length > 0) {
            this.state.selectedYear = this.state.availableYears[0];  // Set the default year to the first available year
            await this.render_invoice_line_chart(this.state.selectedYear);
        }
    }

    // Fetch the available years with data from account.invoice.report
    async loadAvailableYears() {
        const result_data = await jsonrpc("/web/dataset/call_kw/account.invoice.report/search_read", {
            model: 'account.invoice.report',
            method: 'search_read',
            args: [[], ['invoice_date']],
            kwargs: {}
        });

        // Extract the years from the invoice_date field
        const yearsSet = new Set();
        result_data.forEach(record => {
            const year = new Date(record.invoice_date).getFullYear();
            yearsSet.add(year);
        });

        // Sort and update availableYears state
        this.state.availableYears = Array.from(yearsSet).sort((a, b) => b - a);  // Sort by descending order (latest year first)
    }

    // Handle year filter change
    async onYearChange(ev) {
        const selectedYear = ev.target.value;
        this.state.selectedYear = selectedYear;
        await this.render_invoice_line_chart(selectedYear);  // Re-render chart with the new year
    }

    // Render the line chart with dynamic data based on the selected year and the previous year
    async render_invoice_line_chart(year) {
        const chartData = await this.prepareDynamicChartData(year);
        const $el = $(this.invoice_line_chart_ref.el);

        // Destroy the previous chart instance if it exists to prevent reuse errors
        if (this.chartInstance) {
            this.chartInstance.destroy();
        }

        // Create a new chart instance
        this.chartInstance = this.createChart($el, "line", chartData);
    }

    // Fetch dynamic data from the account.invoice.report model for the selected year and the previous year, grouped by month
    async prepareDynamicChartData(year) {
        const previousYear = (parseInt(year) - 1).toString();  // Get the previous year

        // Fetch data for the selected year
        const selectedYearData = await jsonrpc("/web/dataset/call_kw/account.invoice.report/search_read", {
            model: 'account.invoice.report',
            method: 'search_read',
            args: [
                [['invoice_date', '>=', `${year}-01-01`], ['invoice_date', '<=', `${year}-12-31`]],
                ['invoice_date', 'price_total']
            ],
            kwargs: {}
        });

        // Fetch data for the previous year
        const previousYearData = await jsonrpc("/web/dataset/call_kw/account.invoice.report/search_read", {
            model: 'account.invoice.report',
            method: 'search_read',
            args: [
                [['invoice_date', '>=', `${previousYear}-01-01`], ['invoice_date', '<=', `${previousYear}-12-31`]],
                ['invoice_date', 'price_total']
            ],
            kwargs: {}
        });

        // Initialize arrays for months
        const months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
        const selectedYearTotals = Array(12).fill(0);  // Initialize totals for all months (from January to December) with zero
        const previousYearTotals = Array(12).fill(0);  // For previous year

        // Process data for the selected year and sum by month
        selectedYearData.forEach(record => {
            const invoiceMonth = new Date(record.invoice_date).getMonth();  // Get month index (0-11)
            selectedYearTotals[invoiceMonth] += record.price_total;  // Sum totals for the respective month
        });

        // Process data for the previous year and sum by month
        previousYearData.forEach(record => {
            const invoiceMonth = new Date(record.invoice_date).getMonth();  // Get month index (0-11)
            previousYearTotals[invoiceMonth] += record.price_total;  // Sum totals for the respective month
        });

        // Return the formatted data for the line chart
        return {
            labels: months,  // X-axis labels (months from January to December)
            datasets: [
                {
                    label: `Invoice Amount ${year}`,
                    data: selectedYearTotals,  // Y-axis data for the selected year
                    backgroundColor: "rgba(0, 255, 0, 0)",
                    borderColor: "rgba(0, 255, 0, 1)",
                    borderWidth: 1,
                    fill: false
                },
                {
                    label: `Invoice Amount ${previousYear}`,
                    data: previousYearTotals,  // Y-axis data for the previous year
                    backgroundColor: "rgba(255, 0, 0, 0)",
                    borderColor: "rgba(255, 0, 0, 1)",
                    borderWidth: 1,
                    fill: false
                }
            ]
        };
    }

    // Create the chart using Chart.js
    createChart(element, type, data) {
        const config = {
            type: type,
            data: data,
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: `Invoice Analysis Line Chart for ${this.state.selectedYear} and ${parseInt(this.state.selectedYear) - 1}`
                    }
                }
            }
        };
        return new Chart(element, config);  // Store the chart instance
    }
}

InvoiceAnalysisDashboard.template = "InvoiceAnalysisDashboardMain";
registry.category("actions").add("invoice_analysis_dashboard_main", InvoiceAnalysisDashboard);
