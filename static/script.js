$(document).ready(function() {
    const $popupOverlay = $('#popupOverlay');
    const $closePopupButton = $('#closePopup');

    // Show the popup when the page loads
    $('body').addClass('popup-active');

    $closePopupButton.on('click', function() {
        // Hide the popup and enable the rest of the website
        $popupOverlay.hide();
        $('body').removeClass('popup-active');
    });

    var socket = io('https://lucasbertovic-options-77be83cd2d74.herokuapp.com');
    //var socket = io();
    $('#addToPositionButton').on('click', function() {
        // Get the value of the transactionPrice input
        var transactionPrice = $('#transactionPrice').val();

        // Check if the transactionPrice input has a numerical value
        if (transactionPrice && !isNaN(transactionPrice) && transactionPrice > 0) {
            $.ajax({
                url: '/update_option',
                type: 'POST',
                success: function(response) {
                    fetchTableData();
                },
                error: function(error) {
                    console.error('Error updating option:', error);
                }
            });
        } else {
            console.error('Invalid transaction price. Please enter a valid numerical value.');
        }
    });

    $('#clearPositionButton').on('click', function() {
        $.ajax({
            url: '/clear_position',
            type: 'POST',
            success: function(response) {
                if (currentView === 'position1') {
                    $('#position1Content .position-table tbody').children('tr').not('.footer-row').remove();
                } else if (currentView === 'position2') {
                    $('#position2Content .position-table tbody').children('tr').not('.footer-row').remove();
                } else if (currentView === 'position3') {
                    $('#position3Content .position-table tbody').children('tr').not('.footer-row').remove();
                }
            },
            error: function(error) {
                console.error('Error updating option:', error);
            }
        });
    });

    function fetchTableData() {
        $.ajax({
            url: '/get_table_data',
            type: 'GET',
            success: function(data) {
                const tbody = $(`#${currentView}Content .position-table tbody`);
                const footerRow = tbody.find('.footer-row');
                data.forEach(row => {
                    const newRow = `
                        <tr>
                            <td style="text-align: center;">${row.exercise_price}</td>
                            <td style="text-align: center;">${row.type}</td>
                            <td style="text-align: center;">${row.position}</td>
                            <td style="text-align: right;">${row.expirationDate}</td>
                            <td style="text-align: right;">${row.impliedVolatility}</td>
                            <td style="text-align: right;">${row.price_unit}</td>
                            <td style="text-align: right;">${row.quantity}</td>
                            <td style="text-align: right;">${row.total_price}</td>
                            <td style="text-align: right;">${row.theoreticalValue}</td>
                            <td style="text-align: right;">${row.edge}</td>
                            <td style="text-align: right;">${row.delta}</td>
                            <td style="text-align: right;">${row.gamma}</td>
                            <td style="text-align: right;">${row.theta}</td>
                            <td style="text-align: right;">${row.vega}</td>
                            <td style="text-align: right;">${row.rho}</td>
                        </tr>
                    `;
                    footerRow.before(newRow);
                });
            },
            error: function(error) {
                console.error('Error fetching table data:', error);
            }
        });
    }
    

    function updateData() {
        var currentUnderlyingPrice = $('#currentUnderlyingPrice').val();
        var underlyingVolatility = $('#underlyingVolatility').val();
        var currentDateInput = $('#currentDateInput').val();
        var interestRate = $('#interestRate').val();
        
        $.ajax({
            type: 'POST',
            url: '/update_data',
            contentType: 'application/json',
            data: JSON.stringify({
                currentUnderlyingPrice: currentUnderlyingPrice,
                underlyingVolatility: underlyingVolatility,
                currentDateInput: currentDateInput,
                interestRate: interestRate
            }),
            success: function(response) {
                console.log(response.message);
            },
            error: function(error) {
                console.log('Error:', error);
            }
        });
    }

    function update_position_inputter() {
        var transactionDateTime = $('#transactionDatetime').val();
        var expirationDateTime = $('#expirationDatetime').val();
        var optionType = $('#optionType').val();
        var longShort = $('#optionPositionSelection').val();
        var quantity = $('#quantity').val();
        var strikePrice = $('#strikePrice').val();
        var transactionPrice =  $('#transactionPrice').val();
        
        $.ajax({
            type: 'POST',
            url: '/update_position_inputter',
            contentType: 'application/json',
            data: JSON.stringify({
                transactionDateTime: transactionDateTime,
                expirationDateTime: expirationDateTime,
                optionType: optionType,
                longShort: longShort,
                quantity: quantity,
                strikePrice: strikePrice,
                transactionPrice: transactionPrice
            }),
            success: function(response) {
                console.log(response.message);
            },
            error: function(error) {
                console.log('Error:', error);
            }
        });
    }
    
    // Event listeners for input changes
    $('#currentUnderlyingPrice').change(updateData);
    $('#underlyingVolatility').change(updateData);
    $('#currentDateInput').change(updateData);
    $('#currentDateInput').change(updateData);
    $('#interestRate').change(updateData);

    $('#transactionDatetime').change(update_position_inputter);
    $('#expirationDatetime').change(update_position_inputter);
    $('#optionType').change(update_position_inputter);
    $('#optionPositionSelection').change(update_position_inputter);
    $('#quantity').change(update_position_inputter);
    $('#strikePrice').change(update_position_inputter);
    $('#transactionPrice').change(update_position_inputter);

    var lineCharts = [null, null, null, null];

    function fetchChartData(index) {
        $.ajax({
            type: 'GET',
            url: `/chart_data?index=${index}`,
            success: function(data) {
                updateOrCreateChart(index, data.labels, data.datasets, data.title, data.xAxisLabel, data.yAxisLabel);
            },
            error: function(error) {
                console.log(`Error fetching chart data for chart ${index}:`, error);
            }
        });
    }
    
    function updateOrCreateChart(index, labels, datasets, title, xAxisLabel, yAxisLabel) {
        var ctx = document.getElementById(`lineChart${index + 1}`).getContext('2d');
        var chartData = {
            labels: labels,
            datasets: datasets.map((dataset, idx) => ({
                label: dataset.label,
                data: dataset.data,
                fill: false,
                borderColor: getSeriesColor(idx), 
                tension: 0.1,
                pointRadius: 2, 
                pointHoverRadius: 4 
            }))
        };
        var options = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: title,
                    font: {
                        size: 14, 
                        weight: 'bold' 
                    },
                    color: '#b3b3b3' 
                },
                legend: {
                    display: false,
                    position: 'top'
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: xAxisLabel 
                    },
                    ticks: {
                        callback: function(value, index, values) {
                            // Show label at every 10 integers and the last label
                            if (index % 10 === 0 || index === labels.length - 1) {
                                return labels[index];
                            }
                            return '';
                        }
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: yAxisLabel 
                    }
                }
            }
        };
    
        // Destroy existing chart instance if exists
        if (lineCharts[index]) {
            lineCharts[index].destroy();
        }
    
        // Create a new chart instance
        lineCharts[index] = new Chart(ctx, {
            type: 'line',
            data: chartData,
            options: options
        });
    }

    

    socket.on('updateSpecificChart', function(message) {
        var index = message.index;
        var data = message.data;
        updateOrCreateChart(index, data.labels, data.datasets, data.title, data.xAxisLabel, data.yAxisLabel);
    });
    

    socket.on('update_chart', function(data) {
        updateChartData(data.index, data.labels, data.datasets);
    });

    function updateChartData(index, labels, datasets) {
        var chart = lineCharts[index];
        if (chart) {
            chart.data.labels = labels;
            datasets.forEach((dataset, idx) => {
                chart.data.datasets[idx].data = dataset.data;
            });
            chart.update();
        } else {
            console.log(`Chart ${index} not found`);
        }
    }

    socket.on('update_theoretical_value', function(data) {
        $('#theoreticalValue').val(data.theoreticalValue);
    });

    socket.on('update_table', function(data) {
        // Update table for position 1
        const tbody1 = $('#position1Content .position-table tbody');
        const footerRow1 = tbody1.find('.footer-row');
        tbody1.children('tr').not('.footer-row').remove();
        data.position1.forEach(row => {
            const newRow = `
                <tr>
                    <td style="text-align: center;">${row.exercise_price}</td>
                    <td style="text-align: center;">${row.type}</td>
                    <td style="text-align: center;">${row.position}</td>
                    <td style="text-align: right;">${row.expirationDate}</td>
                    <td style="text-align: right;">${row.impliedVolatility}</td>
                    <td style="text-align: right;">${row.price_unit}</td>
                    <td style="text-align: right;">${row.quantity}</td>
                    <td style="text-align: right;">${row.total_price}</td>
                    <td style="text-align: right;">${row.theoreticalValue}</td>
                    <td style="text-align: right;">${row.edge}</td>
                    <td style="text-align: right;">${row.delta}</td>
                    <td style="text-align: right;">${row.gamma}</td>
                    <td style="text-align: right;">${row.theta}</td>
                    <td style="text-align: right;">${row.vega}</td>
                    <td style="text-align: right;">${row.rho}</td>
                </tr>
            `;
            footerRow1.before(newRow);
        });
    
        // Update table for position 2
        const tbody2 = $('#position2Content .position-table tbody');
        const footerRow2 = tbody2.find('.footer-row');
        tbody2.children('tr').not('.footer-row').remove();
        data.position2.forEach(row => {
            const newRow = `
                <tr>
                    <td style="text-align: center;">${row.exercise_price}</td>
                    <td style="text-align: center;">${row.type}</td>
                    <td style="text-align: center;">${row.position}</td>
                    <td style="text-align: right;">${row.expirationDate}</td>
                    <td style="text-align: right;">${row.impliedVolatility}</td>
                    <td style="text-align: right;">${row.price_unit}</td>
                    <td style="text-align: right;">${row.quantity}</td>
                    <td style="text-align: right;">${row.total_price}</td>
                    <td style="text-align: right;">${row.theoreticalValue}</td>
                    <td style="text-align: right;">${row.edge}</td>
                    <td style="text-align: right;">${row.delta}</td>
                    <td style="text-align: right;">${row.gamma}</td>
                    <td style="text-align: right;">${row.theta}</td>
                    <td style="text-align: right;">${row.vega}</td>
                    <td style="text-align: right;">${row.rho}</td>
                </tr>
            `;
            footerRow2.before(newRow);
        });
    
        // Update table for position 3
        const tbody3 = $('#position3Content .position-table tbody');
        const footerRow3 = tbody3.find('.footer-row');
        tbody3.children('tr').not('.footer-row').remove();
        data.position3.forEach(row => {
            const newRow = `
                <tr>
                    <td style="text-align: center;">${row.exercise_price}</td>
                    <td style="text-align: center;">${row.type}</td>
                    <td style="text-align: center;">${row.position}</td>
                    <td style="text-align: right;">${row.expirationDate}</td>
                    <td style="text-align: right;">${row.impliedVolatility}</td>
                    <td style="text-align: right;">${row.price_unit}</td>
                    <td style="text-align: right;">${row.quantity}</td>
                    <td style="text-align: right;">${row.total_price}</td>
                    <td style="text-align: right;">${row.theoreticalValue}</td>
                    <td style="text-align: right;">${row.edge}</td>
                    <td style="text-align: right;">${row.delta}</td>
                    <td style="text-align: right;">${row.gamma}</td>
                    <td style="text-align: right;">${row.theta}</td>
                    <td style="text-align: right;">${row.vega}</td>
                    <td style="text-align: right;">${row.rho}</td> 
                </tr>
            `;
            footerRow3.before(newRow);
        });
    });
   

    // Function to get color based on series index
    function getSeriesColor(seriesIndex) {
        const colors = ['rgb(255, 28, 28)', 'rgb(21, 124, 21)', 'rgb(39, 151, 255)'];
        return colors[seriesIndex] || 'rgb(200, 200, 200)'; 
    }

    // Initial data fetch for all charts
    for (let i = 0; i < lineCharts.length; i++) {
        fetchChartData(i);
    }
    var currentView = 'greeks';
    function updateView(view) {
        currentView = view;
        socket.emit('button_clicked', { view: view });
    }


    $('.greeks-button').click(function() {
        hideAllContents(); 
        $('#greeksContent').show();
        updateView('greeks'); 
    });

    $('.position1-button').click(function() {
        $('.position-button-group button').css('border', '2px solid rgb(255, 28, 28)');
        hideAllContents(); 
        $('#positionBanner').show(); 
        $('#positionContainer').show();
        $('#position2Content').hide();
        $('#position3Content').hide(); 
        $('#position1Content').show(); 
        updateView('position1');
    });

    $('.position2-button').click(function() {
        $('.position-button-group button').css('border', '2px solid rgb(21, 124, 21)');
        hideAllContents(); 
        $('#positionBanner').show(); 
        $('#positionContainer').show();
        $('#position1Content').hide();
        $('#position3Content').hide(); 
        $('#position2Content').show(); 
        updateView('position2');
    });

    $('.position3-button').click(function() {
        $('.position-button-group button').css('border', '2px solid rgb(39, 151, 255)');
        hideAllContents(); 
        $('#positionBanner').show(); 
        $('#positionContainer').show();
        $('#position1Content').hide();
        $('#position2Content').hide();  
        $('#position3Content').show();
        updateView('position3');
    });

    function hideAllContents() {
        $('.main-content > div').hide(); 
        $('#positionBanner').hide(); 
    }

    socket.on('updateP1Totals', function(data) {
        $('.p1totalQuantity').text(data[0]);
        $('.p1totalPrice').text(data[1]);
        $('.p1totalTheoreticalValue').text(data[2]);
        $('.p1totalIntrinsicValue').text(data[3]);
        $('.p1totalDelta').text(data[4]);
        $('.p1totalGamma').text(data[5]);
        $('.p1totalTheta').text(data[6]);
        $('.p1totalVega').text(data[7]);
        $('.p1totalRho').text(data[8]);
    });

    socket.on('updateP2Totals', function(data) {
        $('.p2totalQuantity').text(data[0]);
        $('.p2totalPrice').text(data[1]);
        $('.p2totalTheoreticalValue').text(data[2]);
        $('.p2totalIntrinsicValue').text(data[3]);
        $('.p2totalDelta').text(data[4]);
        $('.p2totalGamma').text(data[5]);
        $('.p2totalTheta').text(data[6]);
        $('.p2totalVega').text(data[7]);
        $('.p2totalRho').text(data[8]);
    });

    socket.on('updateP3Totals', function(data) {
        $('.p3totalQuantity').text(data[0]);
        $('.p3totalPrice').text(data[1]);
        $('.p3totalTheoreticalValue').text(data[2]);
        $('.p3totalIntrinsicValue').text(data[3]);
        $('.p3totalDelta').text(data[4]);
        $('.p3totalGamma').text(data[5]);
        $('.p3totalTheta').text(data[6]);
        $('.p3totalVega').text(data[7]);
        $('.p3totalRho').text(data[8]);
    });

    // Object to store current selections
    const selections = {
        dropdown1: "Profit/Loss (Price)",
        dropdown2: "Delta (Price)",
        dropdown3: "Gamma (Price)",
        dropdown4: "Vega (Price)"
    };

    // Function to update the selections object
    function updateSelection(dropdownId, value) {
        selections[dropdownId] = value;
        socket.emit('changeGraphFromDropdown', { dropdownId: dropdownId, value:value });
    }

    // Add event listeners to dropdown items
    document.querySelectorAll('.dropdown-menu a').forEach(item => {
        item.addEventListener('click', function(event) {
            event.preventDefault();
            const dropdownId = this.closest('.dropdown').id;
            const value = this.getAttribute('data-value');
            updateSelection(dropdownId, value);

            // Close the dropdown menu after selection
            this.closest('.dropdown-menu').style.display = 'none';
        });
    });

    document.querySelectorAll('.dropdown-toggle').forEach(button => {
        button.addEventListener('click', function(event) {
            event.stopPropagation();
            const menu = this.nextElementSibling;
            menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
        });
    });
    
    document.addEventListener('click', function() {
        document.querySelectorAll('.dropdown-menu').forEach(menu => {
            menu.style.display = 'none';
        });
    });
});
