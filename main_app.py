with tab1:
        st.markdown("---")
        
        # --- ROBUST WHOLE PAGE 3D INTERACTION ---
        whole_page_3d = """
        <script>
            // Use an interval to find the element if it hasn't loaded yet
            const interval = setInterval(() => {
                // Target the specific Streamlit main container
                const container = window.parent.document.querySelector('.main .block-container');
                
                if (container) {
                    clearInterval(interval);
                    
                    // Apply necessary CSS directly via JS
                    container.style.transition = 'transform 0.1s ease-out';
                    container.style.transformStyle = 'preserve-3d';
                    
                    // Set perspective on the parent for 3D effect
                    container.parentElement.style.perspective = '1500px';

                    window.parent.document.body.addEventListener('mousemove', (e) => {
                        let rect = container.getBoundingClientRect();
                        
                        // Calculate mouse position relative to container center
                        let x = e.clientX - rect.left - rect.width / 2;
                        let y = e.clientY - rect.top - rect.height / 2;
                        
                        // Calculate rotation - subtle effect
                        let rotateY = x / 40; 
                        let rotateX = -y / 40;
                        
                        container.style.transform = `rotateY(${rotateY}deg) rotateX(${rotateX}deg)`;
                    });
                    
                    // Reset on mouse leave
                    window.parent.document.body.addEventListener('mouseleave', () => {
                        container.style.transform = `rotateY(0deg) rotateX(0deg)`;
                        container.style.transition = 'transform 0.5s ease';
                    });
                    
                    window.parent.document.body.addEventListener('mouseenter', () => {
                        container.style.transition = 'transform 0.1s ease-out';
                    });
                }
            }, 100);
        </script>
        """
        # Inject the script (height 0 so it's invisible)
        components.html(whole_page_3d, height=0)

        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.header("Welcome to Gaucho Insights! ৻(  •̀ ᗜ •́  ৻)")
            # ... (rest of your text remains the same)
