// static/designer/js/silhouette_editor.js
document.addEventListener('DOMContentLoaded', function() {
    const canvas = document.getElementById('drawing-canvas');
    const img = document.getElementById('silhouette-image') || document.getElementById('image-placeholder');
    const ctx = canvas.getContext('2d');
    const coloredAreasInput = document.getElementById('colored-areas-input');
    const previewBtn = document.getElementById('preview-btn');
    let isDrawing = false;
    let currentTool = 'rect';
    let coloredAreas = JSON.parse(coloredAreasInput.value || '[]');
    let startX, startY;

    // Initialize canvas
    function initCanvas() {
        if (img.tagName === 'IMG') {
            canvas.width = img.width;
            canvas.height = img.height;
        } else {
            canvas.width = img.offsetWidth;
            canvas.height = img.offsetHeight;
        }
        drawExistingAreas();
    }

    // Draw existing areas
    function drawExistingAreas() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        coloredAreas.forEach(area => {
            if (area.type === 'rect') {
                ctx.fillStyle = 'rgba(0, 0, 255, 0.3)';
                ctx.fillRect(area.x, area.y, area.width, area.height);
                ctx.strokeStyle = 'blue';
                ctx.strokeRect(area.x, area.y, area.width, area.height);
            }
        });
    }

    // Handle image selection
    document.querySelectorAll('.image-option').forEach(option => {
        option.addEventListener('click', function() {
            const imgUrl = this.getAttribute('data-url');
            const imgContainer = document.querySelector('.image-container');
            if (imgContainer) {
                imgContainer.innerHTML = `
                    <img id="silhouette-image" src="${imgUrl}" alt="Silhouette">
                    <canvas id="drawing-canvas"></canvas>
                `;
                // Reinitialize canvas with new image
                const newImg = document.getElementById('silhouette-image');
                const newCanvas = document.getElementById('drawing-canvas');
                const newCtx = newCanvas.getContext('2d');
                newImg.onload = function() {
                    newCanvas.width = this.width;
                    newCanvas.height = this.height;
                    // Reassign references
                    canvas = newCanvas;
                    ctx = newCtx;
                    drawExistingAreas();
                };
            }
        });
    });

    // Set up event listeners
    if (img.tagName === 'IMG') {
        img.onload = initCanvas;
    } else {
        initCanvas();
    }

    canvas.addEventListener('mousedown', startDrawing);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseup', stopDrawing);
    canvas.addEventListener('mouseout', stopDrawing);

    document.getElementById('rect-tool').addEventListener('click', () => {
        currentTool = 'rect';
    });

    document.getElementById('clear-all').addEventListener('click', () => {
        coloredAreas = [];
        drawExistingAreas();
        coloredAreasInput.value = JSON.stringify(coloredAreas);
    });

    previewBtn.addEventListener('click', previewMask);

    function startDrawing(e) {
        isDrawing = true;
        startX = e.offsetX;
        startY = e.offsetY;
    }

    function draw(e) {
        if (!isDrawing) return;

        ctx.clearRect(0, 0, canvas.width, canvas.height);
        drawExistingAreas();

        const currentX = e.offsetX;
        const currentY = e.offsetY;
        const width = currentX - startX;
        const height = currentY - startY;

        if (currentTool === 'rect') {
            ctx.fillStyle = 'rgba(0, 0, 255, 0.3)';
            ctx.fillRect(startX, startY, width, height);
            ctx.strokeStyle = 'blue';
            ctx.strokeRect(startX, startY, width, height);
        }
    }

    function stopDrawing(e) {
        if (!isDrawing) return;
        isDrawing = false;

        const currentX = e.offsetX;
        const currentY = e.offsetY;
        const width = currentX - startX;
        const height = currentY - startY;

        if (Math.abs(width) > 5 && Math.abs(height) > 5) {
            coloredAreas.push({
                type: 'rect',
                x: startX,
                y: startY,
                width: width,
                height: height
            });
            coloredAreasInput.value = JSON.stringify(coloredAreas);
        }
        drawExistingAreas();
    }

    function previewMask() {
        const imgElement = document.getElementById('silhouette-image');
        if (!imgElement) {
            alert('Please select an image first');
            return;
        }

        const imgSrc = imgElement.src;
        const previewWindow = window.open('', 'Mask Preview', 'width=800,height=600');

        if (!previewWindow) {
            alert('Popup window was blocked. Please allow popups for this site.');
            return;
        }

        fetch('/designer/preview-mask-template/')
            .then(response => response.text())
            .then(template => {
                const htmlContent = template
                    .replace('{{image_src}}', imgSrc)
                    .replace('{{colored_areas}}', coloredAreasInput.value);

                previewWindow.document.open();
                previewWindow.document.write(htmlContent);
                previewWindow.document.close();
            });
    }
});