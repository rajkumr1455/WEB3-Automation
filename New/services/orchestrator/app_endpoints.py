    finally:
        ACTIVE_SCANS.dec()


@app.post("/scan", response_model=ScanResponse)
async def start_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """Start a new security scan"""
    scan_id = str(uuid.uuid4())
    
    # Create scan in database
    try:
        scan = create_scan_in_db(
            scan_id=scan_id,
            target_url=request.target_url or "",
            contract_address=request.contract_address or "",
            chain=request.chain,
            scan_config=request.scan_config or {}
        )
        logger.info(f"Created scan {scan_id} for {request.target_url or request.contract_address}")
        
        # Start pipeline in background
        background_tasks.add_task(run_scan_pipeline, scan_id, request)
        
        return ScanResponse(
            scan_id=scan_id,
            status=ScanStatus.PENDING,
            message="Scan started successfully"
        )
    except Exception as e:
        logger.error(f"Failed to create scan: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create scan: {str(e)}")


@app.get("/scan/{scan_id}", response_model=ScanResult)
async def get_scan(scan_id: str):
    """Get scan status and results"""
    scan = get_scan_from_db(scan_id)
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Get all stage results
    stage_results = get_all_stage_results(scan_id)
    
    return ScanResult(
        scan_id=scan.scan_id,
        status=ScanStatus(scan.status.value),
        target_url=scan.target_url or "",
        contract_address=scan.contract_address,
        started_at=scan.started_at.isoformat() if scan.started_at else scan.created_at.isoformat(),
        completed_at=scan.completed_at.isoformat() if scan.completed_at else None,
        duration_seconds=scan.duration_seconds,
        results=stage_results if stage_results else None,
        error=scan.error_message
    )


@app.get("/scans")
