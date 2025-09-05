/*
 Copyright (C) 2025 AIDC-AI
 This project is licensed under the MIT License (SPDX-License-identifier: MIT).
*/

import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { CheckCircle, XCircle, AlertTriangle, Info } from 'lucide-react';

export default function AlertDialog() {
    const [isOpen, setIsOpen] = useState(props.open || false);

    const handleClose = () => {
        setIsOpen(false);
        deleteElement();
    };

    const getIcon = () => {
        switch (props.type) {
            case 'success':
                return <CheckCircle className="h-5 w-5 text-green-500" />;
            case 'error':
                return <XCircle className="h-5 w-5 text-red-500" />;
            case 'warning':
                return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
            default:
                return <Info className="h-5 w-5 text-blue-500" />;
        }
    };

    const getButtonColor = () => {
        switch (props.type) {
            case 'success':
                return '';
            case 'error':
                return 'destructive';
            case 'warning':
                return 'outline';
            default:
                return 'outline';
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        {getIcon()}
                        {props.title || "Alert"}
                    </DialogTitle>
                </DialogHeader>
                
                <div className="py-2">
                    <div className="text-sm text-foreground">
                        {props.message || ""}
                    </div>
                </div>

                <DialogFooter>
                    <Button 
                        variant={getButtonColor()}
                        onClick={handleClose}
                        className="w-full"
                    >
                        Confirm
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
} 